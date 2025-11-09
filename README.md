# Telegram бот профорієнтації — приклад

## Вимоги
- Python 3.10+
- Встановити залежності: `pip install -r requirements.txt`

## Налаштування
1. Скопіювати `.env.example` в `.env` і вставити свій `TG_BOT_TOKEN` та `TG_ADMINS`.
2. Переконайтесь, що папка `data/` містить `menu.json` і `info.json`.

## Запуск локально
```bash
python -m venv venv
source venv/bin/activate    # або venv\\Scripts\\activate на Windows
pip install -r requirements.txt
python bot.py
