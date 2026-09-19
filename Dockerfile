# ============================================================
# dev-app — 單一 container 全棧部署
# nginx (serve 前端 + proxy /api) + uvicorn (後端) 一齊跑
# ============================================================

# ---- Stage 1: build 前端 ----
FROM node:22-alpine AS frontend-build
WORKDIR /app
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# ---- Stage 2: 最終 image ----
FROM python:3.11-slim

# nginx（serve 靜態前端 + reverse proxy）
RUN apt-get update \
    && apt-get install -y --no-install-recommends nginx \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 後端依賴
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# 後端 code
COPY backend/app ./app

# 前端 build 產物
COPY --from=frontend-build /app/dist /usr/share/nginx/html

# nginx + supervisor config
RUN rm -f /etc/nginx/sites-enabled/default
COPY deploy/nginx.conf /etc/nginx/conf.d/default.conf
COPY deploy/supervisord.conf /etc/supervisord.conf

# supervisor（管理 nginx + uvicorn 兩個 process）
RUN pip install --no-cache-dir supervisor

EXPOSE 8080

CMD ["supervisord", "-c", "/etc/supervisord.conf"]
