FROM python:3.12-slim

WORKDIR /app

RUN pip install uv

COPY requirements.txt .
RUN uv pip install --system --no-cache-dir -r requirements.txt

COPY app .

CMD ["streamlit", "run", "app.py", "--server.port=5002", "--server.address=0.0.0.0"]