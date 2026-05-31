FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Le bot tourne en continu (polling) — pas de port web à exposer.
CMD ["python", "bot.py"]
