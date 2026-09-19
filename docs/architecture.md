# Architecture — dev-app

## 技術棧

| 層 | 技術 | 原因 |
|----|------|------|
| **前端** | React 18 + TypeScript + Vite | 主流、PWA 生態好 |
| **PWA** | vite-plugin-pwa（Service Worker） | 離線快取 app shell + 靜態資源 |
| **離線 DB** | IndexedDB（Dexie.js） | 本地儲存，離線讀寫 |
| **樣式** | Tailwind CSS | 快速做 responsive UI |
| **後端** | FastAPI + SQLAlchemy | 同你其他 project 一致 |
| **資料庫** | PostgreSQL（生產）／SQLite（本地 dev） | 團隊多用戶 + sync 需要關聯式 |
| **認證** | JWT（access + refresh token） | 無狀態、啱 PWA |
| **PDF 解析** | PyMuPDF | 同 free-api 一致，純 Python |
| **檔案儲存** | 本地磁碟（images/PDFs）→ 可擴 DO Spaces | 簡單起步 |

## 系統架構

```
┌─────────────────────────────┐        ┌──────────────────────────┐
│  PWA 前端 (React)           │        │  Backend (FastAPI)       │
│                             │        │                          │
│  ┌───────────────┐          │  sync  │  ┌────────────────────┐  │
│  │ React UI      │          │ ◄────► │  │ REST API           │  │
│  └──────┬────────┘          │  push/ │  │ - auth             │  │
│         │                  │  pull  │  │ - styles/samples   │  │
│  ┌──────▼────────┐          │        │  │ - boms/materials   │  │
│  │ Dexie.js      │          │        │  │ - pdf parse        │  │
│  │ (IndexedDB)   │          │        │  │ - images           │  │
│  └──────┬────────┘          │        │  └─────────┬──────────┘  │
│         │  offline queue   │        │            │             │
│  ┌──────▼────────┐          │        │  ┌─────────▼──────────┐  │
│  │ Service Worker│          │        │  │ PostgreSQL          │  │
│  │ (cache shell) │          │        │  │ (source of truth)   │  │
│  └───────────────┘          │        │  └────────────────────┘  │
│                             │        │                          │
│  PDF 解析 = online only     │        │  ┌────────────────────┐  │
└─────────────────────────────┘        │  │ 檔案儲存 (images/pdf)│  │
                                       │  └────────────────────┘  │
                                       └──────────────────────────┘
```

## 數據模型

```
User (用戶)
  id, email, name, password_hash, role(admin/developer/viewer)

Style (鞋款) 1 ──── * Sample (樣本) 1 ──── 1 BOM (物料清單) 1 ──── * BOMItem
  id                 id                    id                     id
  ref_no             style_id              sample_id              bom_id
  customer           stage (enum)          version                component (部件)
  brand              sample_no             notes                  material_id ──┐
  designer           size                                         quantity       │
  season             status                                       unit           │
  category           requested_date                               color          │
  status             received_date                                supplier_ref   │
                     notes                                        remarks        │
                                                                                │
Style 1 ──── * SampleImage (樣本相)                                            │
Style 1 ──── * SpecSheet (PDF規格表)                                          │
                                                                                │
Material (master 物料主檔) ◄────────────────────────────────────────────────────┘
  id, material_code(SKU), name, type(leather/synthetic/textile/rubber/metal...),
  color, color_code, supplier, supplier_ref, unit, price, min_order,
  spec(description), image, status

Component (部件主檔 — 可自訂)
  id, name (Vamp/Quarter/Tongue/Collar/Sole/Midsole/Insole/Lining/Lace/Eyelet...)
```

**關係重點：**
- 一個 `Style` 有多個 `Sample`，對應開發階段（Development → Confirmation → Salesman → Production → Photo）
- 每個 `Sample` 有**自己一份 BOM**（`Sample 1─1 BOM`）
- 每個 `BOM` 有多個 `BOMItem`，每個 item 引用一個 `Material`（從 master 揀）＋一個 `Component`（部件）
- `SampleImage` 掛喺 `Sample`；`SpecSheet` 掛喺 `Style`

## Offline-First 同步設計

**本地優先（local-first）原則：**
1. 所有讀寫都行 **IndexedDB（Dexie.js）**，唔直接等 server
2. 每次寫入：寫 IndexedDB + 標記為 `pending`（待同步）
3. Service Worker 快取 app shell，斷網照開

**Sync 引擎（連網時觸發 + 定時）：**
```
Push（本地 → server）：送 pending 改動（create/update/delete）
Pull（server → 本地）：拉 server 上 sync_timestamp 之後嘅改動
```

**衝突處理：** last-write-wins
- 每條 record 有 `id (UUID)` + `updated_at` + `deleted_at`（soft delete）
- 同步時比較 `updated_at`，新嘅贏
- 刪除用 soft delete（`deleted_at` 標記），唔會物理刪（避免離線衝突）

**PDF 解析例外：** import PDF spec sheet 需要 network（解析喺 server 做 PyMuPDF）。其餘核心操作（BOM／material／sample）全部離線可用。

## PDF Spec Sheet 解析流程

```
上傳 PDF (multipart)
   │
   ▼
Server: PyMuPDF 提取文字
   │
   ▼
解析引擎（regex/keyword 匹配）
   │ 抽：ref no、designer、color、material code/SKU、sizes、dates
   ▼
返回結構化 JSON（parsed fields）
   │
   ▼
前端：預填 Style/BOM 表單，用戶 review/修正
   │
   ▼
確認 → 寫入 Style + BOM（可離線後續編輯）
```

## 部署

- **目標**：DigitalOcean（App Platform 或 droplet + Docker）
- **Frontend**：Vite build 出 static，由 FastAPI 一齊 serve（或分開）
- **Backend**：uvicorn + systemd / App Platform
- **資料庫**：PostgreSQL（DO Managed DB 或 droplet 自裝）
- **反向代理**：Caddy/Nginx + HTTPS（PWA 需要 HTTPS 先用到 service worker）

## 開發階段建議

1. **Phase 1（先出 demo）**：後端 FastAPI + SQLite，前端 React 讀寫，做到 Style/Sample/BOM/Material CRUD ＋ PDF 解析（先唔做 offline）
2. **Phase 2**：加 PWA（service worker + Dexie）＋ sync 引擎，做到 offline-first
3. **Phase 3**：加 auth + 團隊角色權限
4. **Phase 4**：部署 DO（PostgreSQL + HTTPS）

> 註：offline-first 係最複雜嘅部分，建議先出 online 版本嘅 demo（「出黎睇下先」），再加 offline 層。
