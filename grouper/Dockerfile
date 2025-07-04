FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
            libgl1 \
            libglib2.0-0 \
        && rm -rf /var/lib/apt/lists/*
RUN pip install uv

COPY requirements.txt .
RUN uv pip install --system --no-cache-dir -r requirements.txt

COPY app .

CMD ["gunicorn", "--bind", "0.0.0.0:5003", "main:app", "--workers=1", "--threads=1"]