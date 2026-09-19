FROM python:3.11-slim

WORKDIR /app

# 安裝依賴（先 copy requirements 方便用 layer cache）
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app code
COPY app ./app

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
