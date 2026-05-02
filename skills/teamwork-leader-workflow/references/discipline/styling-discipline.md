# Styling Discipline

Applicable to: **UX PM**, **RD PM** (when touching CSS / SCSS / inline styles)

跨框架（Mezzanine、Tailwind、原生 CSS、CSS Modules、styled-components）通用的 styling 紀律。

## 核心原則

寫任何 layout / spacing / visual code 之前，先「找正解」再「打 patch」。

## 觸發警示情境

下列情境必須暫停找根因：

- `*.module.scss` 出現 `margin(-side)?: <非零>px`（不含 `0px` reset）
- `*.module.scss` 出現 `!important`
- `*.tsx` 出現 inline `style={{ ... padding/margin/width/height/top/left/right/bottom/gap... }}` 含 layout 屬性
- 跨檔複製貼上同段 CSS
- 同個 magic number 反覆 iterate（2px → 4px → 8px）
- `transform: translate(-50%)` / `position: absolute; top: -1px` 之類 visual hack
- `z-index` 數值戰爭（`9999` / `99999`）

## 決策樹（動手前）

### 1. 區分症狀 vs 根因

| 症狀（容易做的） | 根因（應找的） |
|---|---|
| 按鈕對不齊 → 加 `padding-bottom` | 為什麼對不齊？align-items 沒設？元件庫有對齊 prop？ |
| Scroll 不順 → 加 `overflow: hidden` | 為什麼？父元素高度沒控制？flex 子項擴張？ |
| 文字超出容器 → 加 `width: 100%` | flex 沒設 `min-width: 0`？ |
| 元素位置不對 → `position: absolute; top: Xpx` | 該用 grid / flex 重組？ |
| 顏色不對 → 加 `!important` | specificity 順序錯？該調整 selector？ |

口訣：每次想加 padding/margin/position/important 之前，先寫一句「我要修的真正問題是 ___」。寫不出 → 停下查。

### 2. 第二次 iterate 警示

剛改過一次效果不對 → **不要繼續調數值**：

- 用錯 layout primitive？（`margin` 該用 `gap`、`padding` 該用 `align-items`）
- 元件庫有沒有對齊 / 間距內建 API？
- 該由父元素或 sibling 元素負責？

### 3. 複製 CSS 警示

同段 CSS 寫第二次（不論同檔、跨檔）→ **不要直接複製**：

- 下沉到共用元件 `.module.scss`
- 抽 SCSS mixin / placeholder selector
- 抽 utility class 到全域 stylesheet
- 用 design token / CSS custom property
- 例外：完全相同但 spec/語意不同 → 加註解說明為何不抽

### 4. `!important` 警示

絕對不主動加。非加不可時：

- 確認是否 specificity 戰爭（更高優先序 selector 在覆蓋）
- 試把 selector 寫具體（多加一層 class）
- 試調整 rule 順序
- 真的要 `!important`：寫在 `overrides.module.scss` 或 inline `// !important required because: <reason>` 註解

### 5. Inline style 警示

`style={{ ... }}` 含 layout 屬性：

- 移到 `*.module.scss` 用 className
- 用元件庫 layout primitive（Section、Stack、Box）
- 例外：值來自 JS runtime 變數 → 用 CSS custom property：
  ```tsx
  style={{ '--col-w': `${dynamicWidth}px` } as React.CSSProperties}
  ```
  配合 `.col { width: var(--col-w); }`
  - 務必帶單位（`${x}px` / `${x}rem`）
  - `--` key 不在 React `CSSProperties` 型別內，需 `as React.CSSProperties` cast

## 決策後

- Commit message / RAID-I / dispatch return 寫「為何選這個方案而不是 X」
- 若繞過警示，evidence 至少寫一句（「已確認元件庫無對應 prop」「已試過 specificity 無法調整」）

## Override

User-level rules at `~/.claude/rules/styling-discipline.md` (if present) take precedence per user-instruction priority. This file is plugin's portable default for users without that file.
