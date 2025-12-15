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
from telegram.ext import ContextTypes, CallbackQueryHandler, CommandHandler
from config import MENU_FILE, INFO_FILE, CB_PREFIX, WELCOME_TEXT

# ===============================================================
# Менеджер меню
# ===============================================================
class MenuManager:
    def __init__(self):
        self.menu = {}
        self.info = {}
        self.load()

    def load(self):
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

    def build_markup(self, node: dict, path: list, row_size: int = 3):

    # ===============================
    # Визначаємо список дочірніх елементів
    # ===============================
        child_list = (
            node.get("buttons") or 
            node.get("items") or 
            node.get("children") or 
            []
        )

        is_main_menu = not path
        custom_layout = node.get("layout")

        kb = []
        buttons = []

    # ===============================
    # Генеруємо кнопки
    # ===============================
        for it in child_list:
            key = it.get("key")
            text = it.get("text", key)

        # --- 1. Якщо кнопка містить прямий URL у JSON
            if "url" in it:
                buttons.append(InlineKeyboardButton(text, url=it["url"]))
                continue

        # --- 2. Якщо кнопка використовує key → дивимось у info.json
            if key:
                info_value = self.info.get(key)

            # Якщо в info.json URL → робимо URL кнопку
                if isinstance(info_value, str) and info_value.startswith(("http://", "https://")):
                    buttons.append(InlineKeyboardButton(text, url=info_value))
                    continue

            # Інакше — callback
                cb = CB_PREFIX + "/".join(path + [key])
                buttons.append(InlineKeyboardButton(text, callback_data=cb))
                continue

    # ===========================================================
    #                 РОЗКЛАДКА ГОЛОВНОГО МЕНЮ
    # ===========================================================
        if is_main_menu:
            main_menu_layout = [1, 2, 2, 1, 3]

            i = 0
            for row_count in main_menu_layout:
                if i >= len(buttons):
                    break
                kb.append(buttons[i:i + row_count])
                i += row_count

        # якщо залишились кнопки
            while i < len(buttons):
                kb.append(buttons[i:i + row_size])
                i += row_size

    # ===========================================================
    #              КАСТОМНИЙ LAYOUT ДЛЯ ПІДМЕНЮ
    # ===========================================================
        elif custom_layout:
            i = 0
            for count in custom_layout:
                if i >= len(buttons):
                    break
                kb.append(buttons[i:i + count])
                i += count

        # добивка
            while i < len(buttons):
                kb.append(buttons[i:i + row_size])
                i += row_size

    # ===========================================================
    #                   СТАНДАРТНИЙ LAYOUT
    # ===========================================================
        else:
            for i in range(0, len(buttons), row_size):
                kb.append(buttons[i:i + row_size])

    # ===========================================================
    #      Кнопки НАЗАД і ГОЛОВНЕ МЕНЮ — завжди поруч
    # ===========================================================
        if path:
            back_cb = CB_PREFIX + "/".join(path[:-1]) if len(path) > 1 else CB_PREFIX
            home_cb = CB_PREFIX

            kb.append([
                InlineKeyboardButton("⬅️ Назад", callback_data=back_cb),
                InlineKeyboardButton("🏠 Головне меню", callback_data=home_cb)
            ])

        return InlineKeyboardMarkup(kb)

    
    def find_node_by_key(self, key: str, node=None):
        if node is None:
            node = self.menu
        if node.get("key") == key:
            return node
        for child in node.get("items", []) + node.get("children", []):
            result = self.find_node_by_key(key, child)
            if result:
                return result
        return None


menu_manager = MenuManager()

# ===============================================================
# Профорієнтаційний тест
# ===============================================================
career_questions = [
    {
        "q": "1️⃣ Що вам більше до душі?",
        "options": {
            "Фізична активність, спорт": "sport_faculty",
            "Історія, культура, суспільство": "history_faculty",
            "Психологія, допомога людям": "psychology_faculty",
            "Мистецтво, малювання, діти": "preschool_education_faculty"
        }
    },
    {
        "q": "2️⃣ Що вам подобається в навчанні?",
        "options": {
            "Розуміти, як щось працює": "teh_faculty",
            "Писати тексти, аналізувати літературу": "philology_faculty",
            "Працювати руками, створювати речі": "teh_faculty",
            "Спілкуватися з людьми": "psychology_faculty"
        }
    },
    {
        "q": "3️⃣ Який урок у школі вам найцікавіший?",
        "options": {
            "Фізкультура": "sport_faculty",
            "Історія": "history_faculty",
            "Психологія / Громадянська освіта": "psychology_faculty",
            "Мова і література": "philology_faculty",
            "Трудове навчання": "teh_faculty",
            "Малювання / Музика": "preschool_education_faculty"
        }
    },
    {
        "q": "4️⃣ Що для вас найважливіше в роботі?",
        "options": {
            "Рух і динаміка": "sport_faculty",
            "Креатив і самовираження": "preschool_education_faculty",
            "Спілкування й допомога людям": "psychology_faculty",
            "Логіка, технології": "teh_faculty"
        }
    },
    {
        "q": "5️⃣ Як ви любите проводити вільний час?",
        "options": {
            "Активно, на свіжому повітрі": "sport_faculty",
            "Читаючи або пишучи": "philology_faculty",
            "Малюючи, співаючи, створюючи щось": "preschool_education_faculty",
            "Розмовляючи з друзями": "psychology_faculty"
        }
    }
]

async def start_career_test(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["career_progress"] = 0
    context.user_data["career_scores"] = {}
    await send_next_question(update, context)

async def send_next_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    i = context.user_data.get("career_progress", 0)
    if i >= len(career_questions):
        scores = context.user_data.get("career_scores", {})
        if not scores:
            await update.effective_message.reply_text("Ви не відповіли на жодне питання 😅")
            return
        best_faculty = max(scores, key=scores.get)
        kb = [[InlineKeyboardButton("➡️ Перейти до факультету", callback_data=f"{CB_PREFIX}/specs/{best_faculty}")]]
        faculty_name = menu_manager.info.get(best_faculty, {}).get("text", best_faculty)
        await update.effective_message.reply_text(
            f"✅ Ви завершили тест!\n\nВам найбільше підходить: *{faculty_name}*",
            reply_markup=InlineKeyboardMarkup(kb),
            parse_mode="Markdown"
        )
        return

    qdata = career_questions[i]
    buttons = [
        [InlineKeyboardButton(text=opt, callback_data=f"career_ans:{fac}")]
        for opt, fac in qdata["options"].items()
    ]
    markup = InlineKeyboardMarkup(buttons)
    msg = update.message or update.callback_query.message
    await msg.reply_text(qdata["q"], reply_markup=markup)

async def handle_career_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data.split("career_ans:")[-1]
    scores = context.user_data.setdefault("career_scores", {})
    scores[data] = scores.get(data, 0) + 1
    context.user_data["career_progress"] = context.user_data.get("career_progress", 0) + 1
    await send_next_question(update, context)

# ===============================================================
# Основне меню
# ===============================================================
async def start_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = WELCOME_TEXT
    markup = menu_manager.build_markup(menu_manager.menu, [])
    if update.message:
        await update.message.reply_text(text, reply_markup=markup)
    elif update.callback_query:
        await update.callback_query.message.edit_text(text, reply_markup=markup)




#=========================
async def safe_edit_text(message, text, reply_markup=None, parse_mode=None):
    if message.text == text:
        text += "\u2063"
    await message.edit_text(text, reply_markup=reply_markup, parse_mode=parse_mode)

#=========================


#========================

#========================

# ===== menu_helpers.py =====


CONTACT_FIELDS = ["phone", "email", "consultant_username", "schedule"]

async def try_show_contacts(node_key, query, markup, info):
    """
    Перевіряє, чи в info[node_key] є контакти, і показує їх.
    Повертає True, якщо контакти показано, False — інакше.
    """
    contacts = info.get(node_key)
    if isinstance(contacts, dict) and any(field in contacts for field in CONTACT_FIELDS):
        txt = "Контакти:\n"
        for field, emoji, label in [
            ("phone", "📞", "Телефон"),
            ("email", "✉️", "Email"),
            ("consultant_username", "💬", "Консультант"),
            ("schedule", "🗓️", "Графік")
        ]:
            if value := contacts.get(field):
                txt += f"{emoji} {label}: {value}\n"
        await safe_edit_text(query.message, txt, reply_markup=markup)
        return True
    return False

async def _delete_prev_image(context: ContextTypes.DEFAULT_TYPE):
    msg_id = context.user_data.get("image_message_id")
    chat_id = context.user_data.get("image_chat_id")
    if msg_id and chat_id:
        try:
            await context.bot.delete_message(chat_id=chat_id, message_id=msg_id)
        except Exception:
            pass  # якщо повідомлення вже видалено або немає доступу
        finally:
            context.user_data["image_message_id"] = None
            context.user_data["image_chat_id"] = None


async def menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data or ""
    if not data.startswith(CB_PREFIX):
        return

    path_raw = data[len(CB_PREFIX):].lstrip("/")
    path = path_raw.split("/") if path_raw else []

    node = menu_manager.get_node_by_path(path)

    # Резервний пошук по ключу в меню
    if node is None and path:
        node = menu_manager.find_node_by_key(path[-1])

    node_key = path[-1] if path else (node.get("key") if node else None)
    markup = menu_manager.build_markup(node or {}, path)

    # видаляємо попередню картинку
    await _delete_prev_image(context)
    # беремо інфо вузла
    node_key = path[-1] if path else None
    node_info = menu_manager.info.get(node_key) if node_key else None

  

    # 🔹 Якщо ключ є в info і там словник контактів
    if node_key and node_key in menu_manager.info:
        if await try_show_contacts(node_key, query, markup, menu_manager.info):
            return

    # Спеціальні випадки
    if node_key == "career_test":
        await start_career_test(update, context)
        return

    if node_key == "consult":
        consult = menu_manager.info.get("contacts", {}).get("consultant_username")
        if consult:
            await query.message.edit_text(f"Зв'язатися з консультантом: {consult}", reply_markup=markup)
            return

    if node_key == "faq":
        faqs = menu_manager.info.get("faq", [])
        if not faqs:
            await query.message.edit_text("FAQ порожній.", reply_markup=markup)
            return
        text = "\n\n".join([f"Q: {f.get('q')}\nA: {f.get('a')}" for f in faqs])
        await query.message.edit_text(text, reply_markup=markup)
        return

    if node_key == "news":
        news = menu_manager.info.get("news", [])
        if not news:
            await query.message.edit_text("Новин немає.", reply_markup=markup)
            return
        lines = [f"{n.get('date')} — {n.get('title')}\n{n.get('text')}" for n in news[:3]]
        await query.message.edit_text("\n\n".join(lines), reply_markup=markup)
        return

    # Підменю
    children = node.get("children") or node.get("items") if node else None
    if children:
        node_info = menu_manager.info.get(node_key) if node_key else None
        info_text = None
        image = None
        if isinstance(node_info, str):
            info_text = node_info
        elif isinstance(node_info, dict):
            info_text = node_info.get("text")
            image = node_info.get("image")
        label = info_text or node.get("text") or node.get("title") or "Оберіть пункт:"
        if image:
            msg_photo = await query.message.reply_photo(photo=image)
            context.user_data["image_message_id"] = msg_photo.message_id
            context.user_data["image_chat_id"] = msg_photo.chat_id
        await query.message.edit_text(label, reply_markup=markup)
        return

    # Leaf node
    content = menu_manager.info.get(node_key) if node_key else None
    if isinstance(content, dict):
        title = content.get("title") or node.get("title") or node.get("text") or "Інформація відсутня."
        description = content.get("description") or content.get("text") or ""
        text = f"*{title}*\n\n{description}" if description else f"*{title}*"
        image = content.get("image")
        images = content.get("images")
        buttons_data = content.get("buttons", [])
        kb = []
        for b in buttons_data:
            if b.get("url"):
                kb.append([InlineKeyboardButton(b["text"], url=b["url"])])
            elif b.get("key"):
                cb = CB_PREFIX + "/" + b["key"]
                kb.append([InlineKeyboardButton(b["text"], callback_data=cb)])
        markup = InlineKeyboardMarkup(kb) if kb else markup

        if image:
            msg_photo = await query.message.reply_photo(photo=image)
            context.user_data["image_message_id"] = msg_photo.message_id
            context.user_data["image_chat_id"] = msg_photo.chat_id
        elif images:
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

        await safe_edit_text(query.message, text, reply_markup=markup)
        return

    if isinstance(content, str):
        await query.message.edit_text(content or "Інформація відсутня.", reply_markup=markup)
        return
    # видаляємо попередню картинку


    # fallback
    await query.message.edit_text("Інформація недоступна.", reply_markup=markup)

def register_handlers(application):
   
    application.add_handler(CommandHandler("career_test", start_career_test))
    application.add_handler(CallbackQueryHandler(handle_career_answer, pattern="^career_ans:"))
    application.add_handler(CallbackQueryHandler(menu_callback, pattern=f'^{CB_PREFIX}'))
