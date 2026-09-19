# dev-app — 鞋類開發數據管理系統

記錄鞋類開發（workshop）嘅數據：BOM、sample 相、material、PDF spec sheet。

## 技術棧

- **前端**：React 18 + Vite
- **後端**：FastAPI + SQLAlchemy + SQLite
- **PDF 解析**：PyMuPDF

## 運行（本地開發）

### 後端

```bash
cd backend
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8010
```

### 前端

```bash
cd frontend
npm install
npm run dev
```

→ 打開 http://localhost:5173

## Docker 部署（單一 container，PostgreSQL）

Root 有一個 `Dockerfile`：build 前端 → 最終 image 用 **supervisord** 同時跑 nginx（serve 前端 + proxy `/api`）+ uvicorn（後端）。一個 container 行晒前後端，DO App Platform 會喺 root 搵到 `Dockerfile` 自動認到 component。

```bash
# 1. build image（喺 repo root）
docker build -t dev-app-full .

# 2. 起 network
docker network create devapp

# 3. 起 PostgreSQL（將 YOUR_PASSWORD 改成你嘅密碼）
docker run -d --name postgres --network devapp \
  -e POSTGRES_USER=devapp \
  -e POSTGRES_PASSWORD=YOUR_PASSWORD \
  -e POSTGRES_DB=devapp \
  -v pgdata:/var/lib/postgresql/data \
  postgres:16-alpine

# 4. 起 app（nginx 喺 8080；DATABASE_URL 指去 postgres）
docker run -d --name devapp --network devapp -p 8080:8080 \
  -e DATABASE_URL=postgresql://devapp:YOUR_PASSWORD@postgres:5432/devapp \
  dev-app-full
```

→ 打開 http://localhost:8080

### 部署到 DigitalOcean App Platform

1. 開一個 App → 揀 GitHub repo（`kelvinlamkiwan/dev-app`）
2. DO 會喺 root 偵測到 `Dockerfile`，自動認做 Web Service（預設 health check port **8080**）
3. 加一個 **Database（PostgreSQL）** component，DO 會自動 inject `DATABASE_URL` env var 入 app container
4. Deploy

> 冇設 `DATABASE_URL` 時自動 fallback SQLite（本地 dev 用 SQLite；生產用 Postgres）。

> 舊有「分開三個 container（postgres + backend + frontend）」嘅起法仍喺 `backend/Dockerfile` 同 `frontend/Dockerfile` 度保留，需要時可獨立 build。

## 功能

- 鞋款（Style）＋ 樣本階段（每階段一份 BOM）
- BOM 編輯（從 master material 揀料）
- 物料主檔（Material master）
- PDF spec sheet import（自動拆解 ref / 顏色 / 物料 / 尺寸）
- Confirmation Sample 確認閘口

## 文檔

見 `docs/`：PRD、User Stories、Architecture。
