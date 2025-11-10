# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Копіюємо файли та встановлюємо залежності
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Виставляємо порт (Render передає свій через ENV PORT)


CMD ["python", "bot.py"]
