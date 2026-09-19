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

## Docker 部署（PostgreSQL，唔使 compose）

```bash
# 1. build image
docker build -t dev-app-backend ./backend
docker build -t dev-app-frontend ./frontend

# 2. 起 network
docker network create devapp

# 3. 起 PostgreSQL（將 YOUR_PASSWORD 改成你嘅密碼）
docker run -d --name postgres --network devapp \
  -e POSTGRES_USER=devapp \
  -e POSTGRES_PASSWORD=YOUR_PASSWORD \
  -e POSTGRES_DB=devapp \
  -v pgdata:/var/lib/postgresql/data \
  postgres:16-alpine

# 4. 起 backend（DATABASE_URL 指去 postgres）
docker run -d --name backend --network devapp \
  -e DATABASE_URL=postgresql://devapp:YOUR_PASSWORD@postgres:5432/devapp \
  dev-app-backend

# 5. 起 frontend
docker run -d --name frontend --network devapp -p 8080:80 dev-app-frontend
```

→ 打開 http://localhost:8080（nginx serve 前端 + proxy `/api` 去 backend）

> 本地 dev（唔用 Docker）仍用 SQLite；冇設 `DATABASE_URL` 時自動 fallback SQLite。

## 功能

- 鞋款（Style）＋ 樣本階段（每階段一份 BOM）
- BOM 編輯（從 master material 揀料）
- 物料主檔（Material master）
- PDF spec sheet import（自動拆解 ref / 顏色 / 物料 / 尺寸）
- Confirmation Sample 確認閘口

## 文檔

見 `docs/`：PRD、User Stories、Architecture。
