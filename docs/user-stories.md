# User Stories — dev-app

格式：`As a [角色], I want [功能], So that [好處]`，附 Acceptance Criteria。

## 模組 A：認證

**US-01** 作為團隊成員，我要用 email + 密碼登入，令數據安全。
- AC：正確 email/password 可登入；錯誤會被拒絕並提示。

**US-02** 作為 Admin，我要管理用戶同角色，令只有獲授權嘅人先用到系統。
- AC：可新增／停用用戶；可改角色（Admin/Developer/Viewer）。

**US-03** 作為 Developer，我登入後只能見到同做到授權範圍內嘅嘢，令權限分明。
- AC：Viewer 睇唔到編輯掣；Admin 見到管理入口。

## 模組 B：Style（鞋款）

**US-04** 作為 Developer，我要建立 Style（ref、客戶、品牌、設計師、季節），令每個開發款式有記錄。
- AC：必填 ref；可存草稿；建立後喺列表見到。

**US-05** 作為 Developer，我要搜尋／篩選 Style（客戶、ref、狀態），令我可以快速搵到個款。
- AC：搜尋框即時過濾；可按客戶／狀態篩選。

## 模組 C：Sample（樣本）＋ 階段

**US-06** 作為 Developer，我要喺每個 Style 建立多個 Sample（對應開發階段），令每階段有獨立記錄。
- AC：可新增階段 Sample；階段顯示為 Development/Confirmation/Salesman/Production/Photo。

**US-07** 作為 Developer，我要記錄 Sample 嘅狀態同日期（要求／收貨），令開發進度清晰。
- AC：可填 status + 日期；列表顯示進度。

## 模組 D：BOM（每階段一份）

**US-08** 作為 Developer，我要喺每個 Sample 建立／編輯自己嘅 BOM，令每階段有獨立物料清單。
- AC：每個 Sample 有自己 BOM；切換階段見唔同 BOM。

**US-09** 作為 Developer，我要喺 BOM 揀物料時從 master material 搜尋選取，令唔使重複手打。
- AC：揀料有搜尋下拉；選中後自動填物料資料。

**US-10** 作為 Developer，我要自由編輯 BOM 行項目（加／刪／改數量顏色／排序），令 BOM 隨時可調。
- AC：可增刪改行項目；可改順序；改動即時保存。

**US-11** 作為 Developer，我要將 Confirmation Sample 嘅 BOM 標記「已確認」，令佢成為進入生產嘅閘口。
- AC：未確認前不能標記該階段完成；確認後有清晰狀態。

## 模組 E：Master Material（物料主檔）

**US-12** 作為 Admin／Developer，我要維護 master material（編號、名稱、類型、顏色、供應商、單位、單價），令物料可跨 BOM 重用。
- AC：可 CRUD 物料；可搜尋／篩選／分類。

**US-13** 作為 Developer，我要喺 master 冇嘅物料時即場新增，令工作唔會中斷。
- AC：揀料時可快速新增物料並即刻選用。

## 模組 F：Sample 圖片

**US-14** 作為 Developer，我要上傳 sample 相（含 caption、類型），令樣本有視覺記錄。
- AC：可上傳多張相；可加 caption；離線時可暫存待同步。

## 模組 G：PDF Spec Sheet Import

**US-15** 作為 Developer，我要上傳客戶 PDF spec sheet 並存底到該 Style，令來源有得追查。
- AC：上傳後 PDF 關聯到 Style；可下載重溫。

**US-16** 作為 Developer，我要系統自動拆解 PDF（抽 ref、顏色、物料、尺寸），令唔使手打。
- AC：上傳後自動解析出欄位；解析結果可預填 Style/BOM。

**US-17** 作為 Developer，我要 review／修正解析結果先存檔，令數據準確。
- AC：解析結果以可編輯表單呈現；確認後先寫入。

## 模組 H：Offline-First（PWA）

**US-18** 作為 Developer，我要冇網都開到 app 並建立／編輯 BOM、加 material、加 sample，令 workshop 冇訊號都做到嘢。
- AC：斷網開到 app；可新增／編輯並存本地；唔會因為斷網而失敗。

**US-19** 作為 Developer，我要有網時自動同步我嘅離線改動，令團隊見到最新數據。
- AC：連網後自動 push/pull；衝突用 last-write-wins；完成後顯示已同步。

**US-20** 作為 Developer，我要見到 sync 狀態（離線／待同步／已同步），令我知道數據有冇保存妥當。
- AC：介面有清晰 sync 指示；待同步數量顯示。

## 非功能

**US-21** 作為用戶，我要喺 tablet／手機用得順，令 workshop 內方便操作。
- AC：responsive 介面；觸控友善（大掣、下拉）。

## 總結表

| 模組 | Stories | 核心 |
|------|---------|------|
| A 認證 | US-01~03 | 登入、角色權限 |
| B Style | US-04~05 | 鞋款 CRUD、搜尋 |
| C Sample | US-06~07 | 階段、狀態日期 |
| D BOM | US-08~11 | 每階段 BOM、揀料、自由編輯、確認閘口 |
| E Material | US-12~13 | 物料主檔 CRUD、即場新增 |
| F 圖片 | US-14 | sample 相 |
| G PDF Import | US-15~17 | 上傳、自動拆解、review |
| H Offline | US-18~20 | 離線可用、自動同步、狀態 |
| 非功能 | US-21 | responsive |
