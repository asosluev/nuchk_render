# handlers/menu.py
"""
Menu handler (webhook-ready). Behavior mirrors polling-version logic:
- nested menu from data/menu.json
- content from data/info.json (supports text, dict{text,image,images}, faq, news)
- image shown above, text+buttons under it
- when navigating, previous image (if any) is deleted
- back-button support
"""

import json
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes, CallbackQueryHandler
from config import MENU_FILE, INFO_FILE, CB_PREFIX, WELCOME_TEXT

# Load manager that can be reloaded by admin
class MenuManager:
    def __init__(self):
        self.menu = {}
        self.info = {}
        self.load()

    def load(self):
        # load menu.json and info.json
        with open(MENU_FILE, "r", encoding="utf-8") as f:
            self.menu = json.load(f)
        with open(INFO_FILE, "r", encoding="utf-8") as f:
            self.info = json.load(f)

    def get_node_by_path(self, path: list):
        node = self.menu
        if not path:
            return node
        items = node.get("items", [])
        for key in path:
            found = None
            for it in items:
                if it.get("key") == key:
                    found = it
                    break
            if not found:
                return None
            node = found
            items = node.get("children", []) or node.get("items", [])
        return node

    def build_markup(self, node: dict, path: list):
        kb = []
        child_list = node.get("items") or node.get("children") or []
        for it in child_list:
            key = it.get("key")
            text = it.get("text", key)
            cb = CB_PREFIX + "/".join(path + [key]) if (path or key) else CB_PREFIX
            kb.append([InlineKeyboardButton(text, callback_data=cb)])
        if path:
            back_cb = CB_PREFIX + "/".join(path[:-1]) if len(path) > 1 else CB_PREFIX
            kb.append([InlineKeyboardButton("⬅️ Назад", callback_data=back_cb)])
        return InlineKeyboardMarkup(kb)

menu_manager = MenuManager()

# Start / show root menu
async def start_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = WELCOME_TEXT
    markup = menu_manager.build_markup(menu_manager.menu, [])
    if update.message:
        await update.message.reply_text(text, reply_markup=markup)
    elif update.callback_query:
        await update.callback_query.message.edit_text(text, reply_markup=markup)

# Helper: safely delete stored image message (if any)
async def _delete_prev_image(context: ContextTypes.DEFAULT_TYPE):
    img_id = context.user_data.get("image_message_id")
    chat_id = context.user_data.get("image_chat_id")
    if img_id and chat_id:
        try:
            await context.bot.delete_message(chat_id=chat_id, message_id=img_id)
        except Exception:
            pass
        context.user_data.pop("image_message_id", None)
        context.user_data.pop("image_chat_id", None)

# Main callback handler
async def menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data or ""
    if not data.startswith(CB_PREFIX):
        # ignore unrelated callbacks
        return

    # compute path list
    path_raw = data[len(CB_PREFIX):].lstrip("/")
    path = path_raw.split("/") if path_raw else []

    node = menu_manager.get_node_by_path(path)
    if node is None:
        await query.message.edit_text("Пункт не знайдено.")
        return

    node_key = node.get("key")
    content = menu_manager.info.get(node_key) if node_key else None
    markup = menu_manager.build_markup(node, path)

    # If there was a previously shown image, delete it now (we will show new image if needed)
    await _delete_prev_image(context)

    # Special: consult -> show contact inline
    if node_key == "consult":
        consult = menu_manager.info.get("contacts", {}).get("consultant_username")
        if consult:
            await query.message.edit_text(f"Зв'язатися з консультантом: {consult}", reply_markup=markup)
            return
        contacts = menu_manager.info.get("contacts", {})
        txt = "Контакти:\n"
        if contacts.get("phone"):
            txt += f"Телефон: {contacts.get('phone')}\n"
        if contacts.get("email"):
            txt += f"Email: {contacts.get('email')}\n"
        await query.message.edit_text(txt, reply_markup=markup)
        return

    # Special: faq
    if node_key == "faq":
        faqs = menu_manager.info.get("faq", [])
        if not faqs:
            await query.message.edit_text("FAQ порожній.", reply_markup=markup)
            return
        text = "\n\n".join([f"Q: {f.get('q')}\nA: {f.get('a')}" for f in faqs])
        await query.message.edit_text(text, reply_markup=markup)
        return

    # Special: news (top 3)
    if node_key == "news":
        news = menu_manager.info.get("news", [])
        if not news:
            await query.message.edit_text("Новин немає.", reply_markup=markup)
            return
        lines = []
        for n in news[:3]:
            lines.append(f"{n.get('date')} — {n.get('title')}\n{n.get('text')}")
        await query.message.edit_text("\n\n".join(lines), reply_markup=markup)
        return

    # If node has children -> show submenu (use info text if available)
    children = node.get("children") or node.get("items")
    if children:
        # if info for this node is a string, show it; if dict with text, use it
        info_text = None
        image = None
        if node_key:
            node_info = menu_manager.info.get(node_key)
            if isinstance(node_info, str):
                info_text = node_info
            elif isinstance(node_info, dict):
                info_text = node_info.get("text")
                image = node_info.get("image")
        label = info_text or node.get("text") or node.get("title") or "Оберіть пункт:"
         # ⬇️ якщо є image — показати її
        if image:
            msg_photo = await query.message.reply_photo(photo=image)
            context.user_data["image_message_id"] = msg_photo.message_id
            context.user_data["image_chat_id"] = msg_photo.chat_id
        await query.message.edit_text(label, reply_markup=markup)
        return

    # Leaf node (no children)
    # If content is dict -> may have image/images and text
    if isinstance(content, dict):
        text = content.get("text", "") or node.get("text") or "Інформація відсутня."
        image = content.get("image")
        images = content.get("images")

        # If there is image(s) -> send photo(s) first (top), then edit text message to show text+buttons
        if image:
            # send photo (top)
            msg_photo = await query.message.reply_photo(photo=image)
            # store photo id to delete later
            context.user_data["image_message_id"] = msg_photo.message_id
            context.user_data["image_chat_id"] = msg_photo.chat_id
            # edit the current message (the inline) to the text under the photo
            await query.message.edit_text(text, reply_markup=markup)
            return
        if images:
            # send images; store first image id
            first_id = None
            first_chat = None
            for i, img in enumerate(images):
                msg = await query.message.reply_photo(photo=img)
                if i == 0:
                    first_id = msg.message_id
                    first_chat = msg.chat_id
            if first_id:
                context.user_data["image_message_id"] = first_id
                context.user_data["image_chat_id"] = first_chat
            await query.message.edit_text(text, reply_markup=markup)
            return

        # dict without image -> just edit text
        await query.message.edit_text(text, reply_markup=markup)
        return

    # If content is a string -> simple edit
    if isinstance(content, str):
        await query.message.edit_text(content or "Інформація відсутна.", reply_markup=markup)
        return

    # fallback
    await query.message.edit_text(node.get("text") or "Інформація недоступна.", reply_markup=markup)

def register_handlers(application):
    application.add_handler(CallbackQueryHandler(menu_callback, pattern=f'^{CB_PREFIX}'))
