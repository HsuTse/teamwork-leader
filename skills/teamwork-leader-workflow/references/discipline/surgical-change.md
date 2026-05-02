# Surgical Change Discipline

Applicable to: **RD PM** (and any role making code edits)

## Core principle

A surgical change touches **only what the dispatch's stated scope demands**. Adjacent code stays untouched even if "obviously improvable".

## Rules

- 不要順手「改善」相鄰程式碼、註解或格式
- 不要重構沒壞的東西
- 即使自己會寫不同風格，也要 match 既有 style
- 若發現無關的死碼，提及它（在 return contract `raid_updates` 開 RAID-I），不要自行刪除
- 僅清除「本次變更造成」的孤兒（imports / variables / functions）；pre-existing 死碼需明確批准才刪
- 自我檢查：每一行改動是否都能 trace 回 dispatch's stated scope？

## Why this matters

PM dispatch 的 scope_confidence (per `dispatch-header.md` §`meta` block) 直接量測 surgical-change 紀律。Out-of-scope 改動會：

1. 觸發 `actual_diff_outside_scope = true` → Rule 0 Watch/Escalate
2. 把 `kmr_proxy.scope_surprise` 推升 → 觸發 Mini Gate_Forward
3. 在 cross-PM verification 時被 sibling PM 質疑 → trust_tier demote 風險

## Out-of-scope discoveries 處理

當 PM 在 dispatch 過程中發現「本來不在 scope 但確實該動」的東西：

1. **不要動** — 完成 stated scope 後，在 return contract `raid_updates` 開 RAID-I（issue）
2. RAID-I 內容說明：「<artifact path / line> exhibits <issue>; out of this dispatch's scope; recommend addressed in <next stage / separate dispatch>」
3. TeamLead 收 RAID-I 後決定是否走 CCB-Light / CCB-Heavy 把它 escalate 為 next dispatch 範圍

## Override

User-level rules at `~/.claude/rules/CONTRIBUTING.md` (if present) take precedence per user-instruction priority. This file is plugin's portable default for users without that file.
