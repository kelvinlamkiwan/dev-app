# dev-app — 鞋類開發數據管理系統

## 項目概述

一個 full-stack 應用，俾鞋類開發團隊（developer）喺 workshop 造鞋時，記錄開發數據：**BOM（物料清單）、sample 相、規格表（spec sheet）** 等。支援**離線（offline-first）＋ 在線（online sync）**，可以 import 客戶 PDF spec sheet 自動拆解內容，並從 **master material data** 揀物料，減少重複輸入。

## 背景

- 領域：鞋類開發（NOVI Footwear，客戶如 ZARA / DEPORTIVOS 運動鞋）
- 現況：開發數據以試算表／PDF 技術單管理，容易重複輸入、版本混亂
- 目標：一個結構化、可離線、團隊共用嘅記錄系統

## 用戶角色

| 角色 | 權限 |
|------|------|
| **Admin** | 管理用戶、管理 master material、所有功能 |
| **Developer** | 建立／編輯 Style、Sample、BOM、import spec sheet、加 material |
| **Viewer** | 唯讀（睇 data，唔改得） |

## 核心功能（按模組）

### 1. 認證（Auth）
- 團隊成員 email + 密碼登入（JWT）
- 角色權限控制（Admin / Developer / Viewer）

### 2. Style（鞋款）
- 建立／編輯鞋款：Reference、客戶、品牌、設計師、季節、類別、狀態
- 搜尋／篩選（按客戶、ref、狀態）

### 3. Sample（樣本）＋ 階段
- 每個 Style 有多個 Sample，對應開發階段：**Development → Confirmation → Salesman → Production → Photo**（可自訂）
- 每個階段獨立記錄：樣本編號、size、狀態、要求日期、收貨日期、備註
- **Confirmation Sample 為關鍵閘口**：BOM 必須「確認」先可進入生產／ERP

### 4. BOM（物料清單）— 每階段一份
- 每個 Sample（即每個階段）有自己一份 BOM
- BOM 行項目：**部件（component）＋ 物料（從 master 揀）＋ 數量＋ 單位＋ 顏色＋ 備註**
- 自由編輯：加／刪／改／排序行項目
- 揀物料時從 master material 搜尋選取（唔使手打）

### 5. Master Material Data（物料主檔）
- 物料欄位：物料編號（SKU）、名稱、類型（皮革／合成／織物／橡膠／金屬…）、顏色、色碼、供應商、供應商 ref、單位、單價、最小訂量、規格描述、圖片
- 可喺 BOM 揀料時即場新增物料

### 6. Sample 圖片
- 上傳／附加 sample 相（含 caption、類型：外觀／細節／瑕疵）

### 7. PDF Spec Sheet Import（自動拆解）
- 上傳客戶 PDF 規格表，存底到該 Style
- **自動拆解**：用 PyMuPDF 提取文字，解析 ref、設計師、顏色、物料編號、尺寸、日期等，預填 Style／BOM 欄位
- 用戶**review／修正**解析結果先存檔

### 8. Offline-First（PWA）
- 冇網絡都開到 app、建立／編輯 BOM、加物料、加 sample
- 有網自動 sync（push 本地改動、pull 團隊最新）
- 顯示 sync 狀態（離線／待同步／已同步）

## 非功能需求

- **Offline-first**：核心操作（BOM／material／sample 建立編輯）必須離線可用
- **Responsive**：tablet／手機喺 workshop 用得順
- **數據一致性**：多人同時編輯要有 conflict 處理（last-write-wins）
- **PDF 解析**：需要網絡（解析喺 server 做）；其餘功能離線可用

## 範圍外（呢個 project 唔做）

- 稅務／會計（交俾 ERP）
- 訂單／庫存／生產排程（屬 ERP／MRP）
- 客戶／供應商 portal（可日後擴展）
