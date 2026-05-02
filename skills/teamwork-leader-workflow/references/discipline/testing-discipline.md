# Testing Discipline

Applicable to: **QA PM**, **RD PM**

## Core principles

- 使用專案既有 testing framework；不發明專案不支援的 flags
- 優先驗證真實行為，而非實作細節
- 除非隔離需求明確，否則減少 mocking
- 邏輯變更應新增或更新 automated tests
- 若無法測試，明確說明原因

## Verification 策略選擇

依變更範圍選最快且有意義的驗證：

1. 目標明確的 unit / integration test
2. 相關 lint rule 或 typecheck
3. build 驗證
4. 風險足夠高時才跑 regression suite

不要在沒必要時預設執行最大 test suite。

## Test 品質規則

- 每個 test 驗證 observable behavior
- 避免 tautological assertions（`expect(x).toBe(x)`）
- 避免沒有 assertion 的 test
- 不得把 `console.log`、截圖或推論視為正確性證據
- Hardcoded data 標明為 fixture / seed / mock + 用途

## Red-Green workflow（非 trivial 邏輯變更）

1. 先寫 failing test 證明 bug / missing behavior 存在（red）
2. 改實作讓 test 通過（green）
3. 必要時 refactor

可接受的替代方式（無法嚴格 red-green 時）：
- 重現既有 failing regression，再修
- 在修正旁加明確 negative case
- 先展示 type-level failure，再完成實作

## 目標導向驗證（Goal-Driven Execution）

把命令式需求轉成可觀察測試結果：

- 「加驗證」→「寫 invalid inputs test，再讓它通過」
- 「修 bug」→「寫可重現該 bug 的 test，再讓它通過」
- 「重構 X」→「確認重構前後 test 皆通過」
- 「優化效能」→「定義 baseline 數值與驗證指令，再優化」

多步驟計畫格式：
```
1. [步驟] → verify: [可觀察檢查 / test name / command / 預期輸出]
2. [步驟] → verify: [...]
```

**強 vs 弱成功條件**：
- 強（PM 可自主 loop）：具體 test、明確 command、可觀察輸出
- 弱（PM 應停下來釐清）：「讓它動起來」「變好一點」「沒 bug」

## Coverage

- 若專案既有流程包含 coverage，盡量納入
- 不發明專案不支援的 coverage flags
- 略過時要說明原因

## 驗證失敗時

- 單一明確錯誤 + 修復安全清楚 → 修一次重跑
- 多重失敗 / 雜訊 / 疑似 pre-existing → 停下整理：執行的 command、哪些失敗、是否 pre-existing、建議下一步

連續 auto-fix 嘗試不超過 2 輪。

## 驗證回報（return contract `verify_evidence`）

- 列實際 command
- 保留關鍵輸出
- 標 pass / fail
- 說明未驗證的風險

## Override

This file is the plugin's portable default. If your team has different testing conventions, document overrides in your project's `CLAUDE.md` — agents follow project CLAUDE.md ahead of plugin defaults per Claude Code's standard precedence.
