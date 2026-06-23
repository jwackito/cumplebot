FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt watchfiles

COPY . .

CMD ["watchfiles", "python -m bot.main", "bot", "db"]
