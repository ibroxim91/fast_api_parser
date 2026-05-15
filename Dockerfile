FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Playwright brauzer binarlari
RUN python -m playwright install --with-deps

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8089"]
