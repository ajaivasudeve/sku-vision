FROM python:3.12-slim

WORKDIR /app

RUN pip install uv

COPY requirements.txt .
RUN uv pip install --system --no-cache-dir -r requirements.txt

COPY app .

CMD ["gunicorn", "--bind", "0.0.0.0:5001", "main:app", "--workers=1", "--threads=1"]