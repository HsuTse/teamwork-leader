# Mezzanine UI Discipline

Applicable to: **UX PM**, **RD PM** (Mezzanine projects only)

## When does this apply

Only when project imports `@mezzanine-ui/react`（或 `@mezzanine-ui/react-vue` 等 Mezzanine 衍生套件）。非 Mezzanine 專案 → skip 整段。

## 核心原則

寫任何 Mezzanine 元件 code 之前，**先驗證 API**，不要套標準 React/HTML 慣例。

## 強制檢查項

### 1. Prop 名稱必查 source

Mezzanine 使用大量非標準命名，**禁止憑記憶或標準 React 慣例假設**：

- **`readonly`（小寫，僅限 Mezzanine 元件）**：
  - Mezzanine `<TextField>` 及衍生元件（Select、Search、PasswordField）用小寫 `readonly`
  - 原生 `<input>` / `<textarea>` 仍是駝峰 `readOnly`
  - 判斷依據：import 來源是 `@mezzanine-ui/react` → 用小寫；否則 → 用駝峰
- **Button `size` 用 `GeneralSize`（`'main' | 'sub' | 'minor'`）**：
  - Mezzanine 尺寸命名是「**語意角色**」（main/sub/minor），不是「視覺尺寸」（small/medium/large）
  - 同頁主操作只能有一個 `main`
  - 此語意命名也適用 ContentHeader、Typography 等其他 Mezzanine 元件
- 部分元件用 kebab-case 屬性，不是 camelCase

**查詢順序**：
1. 本機 `node_modules/@mezzanine-ui/react/dist/**/*.d.ts`（最快、最準）
2. 專案的 Storybook URL（若有）— 由 CEO 在 dispatch intake 提供；若 sandbox 擋住 WebFetch 請 CEO 貼連結內容

### 2. 禁止用 `as any` 繞過型別錯誤

型別錯就代表 prop 用錯，回去查 API。`as any` 只是把 build error 拖到 runtime。

### 3. FormField 對齊用 `controlFieldSlotLayout='sub'`

- 禁止用 `padding-bottom` hack 處理 button 與 sibling input 對齊
- Magic number（2px → 4px → 8px）出現第二次就停手找正解
- 對齊類問題的正解通常是 Mezzanine 內建 layout prop，不是自加 padding/margin

### 4. PageHeader 不要包 ContentHeader

- PageHeader 對 ContentHeader children 有觀察到的 size override 行為
- 要 sub 級別標題 → 繞過 PageHeader，直接用 `<ContentHeader size='sub' />`
- 升級 Mezzanine 版本時重新驗證此行為是否仍成立

## 共用樣式收斂

- 多頁面重複的 section CSS（`.tableWrapper`、白卡 padding、filter bar 樣式）→ **下沉到共用元件**（DataTable、PageContainer、FilterArea）內
- 不要在 N 個 `*.module.scss` 各複製一份
- 改動共用元件視覺前，先 grep 列出所有 consumer 評估影響
- consumer 中有 raw `<Table>` 不經 DataTable → 個別保留 local style

## Anti-patterns（不得自行決定）

需先在 RAID-I 開議題給 CEO 決定，不得自己組或繞過：

- 新增 Mezzanine 沒對應的元件（不要自己用 `<div>` 組類似元件）
- 改 design token / 全域 SCSS / theme override
- 直接操作 Mezzanine 內部 class name（`.mzn-*`）
- 為塞自訂行為 fork Mezzanine 元件

## Why this discipline

Mezzanine API 假設錯誤跨多 session 造成的痛點：

- Build 失敗（`readonly` vs `readOnly`、Button size 套 small/medium/large）
- Padding hack 反覆（2px → 4px → 8px，正解是 `controlFieldSlotLayout='sub'`）
- CSS 重複進 N 個 `*.module.scss`，最後重構收斂到共用元件
- PageHeader silently override ContentHeader size

是 Mezzanine 專案摩擦最高的單一來源。

## How to apply

任何下列情況套用：

- 任何 import `@mezzanine-ui/react` 的檔案
- 任何 `mzn-*` CSS class 出現的地方
- 任何專案內部的 Mezzanine wrapper-package 變更（若專案有）
- 對話中提到「按鈕對齊」「FormField」「DataTable」「filter bar」「白卡 layout」等 Mezzanine 領域詞彙時

寫前依序：

1. 取得當前元件 API reference（不憑記憶）— `.d.ts` 檔 grep
2. 涉及頁面組合決策時，問 CEO 是否有既定 pattern
3. 涉及視覺規範或文案時，問 CEO

「我記得 Mezzanine 的 X 是 Y」是 anti-pattern。每次寫前都當作第一次寫，跑完驗證才動手。

## Override

This file is the plugin's portable default for Mezzanine projects. If your team has different Mezzanine conventions, document overrides in your project's `CLAUDE.md` — agents follow project CLAUDE.md ahead of plugin defaults per Claude Code's standard precedence. Skip entirely on non-Mezzanine projects.
