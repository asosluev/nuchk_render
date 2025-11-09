# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Копіюємо файли та встановлюємо залежності
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Виставляємо порт (Render використовує змінну PORT)
ENV PORT=8443

CMD ["python", "bot.py"]
