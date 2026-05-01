# teamwork-leader

> 多 agent PMP 專案編排：TeamLead 統籌 PO/RD/QA/UX/Ad-hoc 角色 PM，透過 stage-gated 流程與三道驗證閘執行專案。

[![version](https://img.shields.io/badge/version-0.1.1-blue.svg)](./.claude-plugin/plugin.json)
[![license](https://img.shields.io/badge/license-MIT-green.svg)](./LICENSE)

---

## 這是什麼

`teamwork-leader` 是一個 [Claude Code](https://claude.com/claude-code) plugin，把單一 Claude session 變成一個小型專案組織：

- **TeamLead**（你 + 此 plugin 的 skill）—— 專案編排者，管理 stage、預算、RAID、CCB
- **CEO**（使用者）—— 在三道 gate 給出 approve / revise / abort 等決策
- **PMs**（5 個 agent：PO / RD / QA / UX / Ad-hoc）—— 各司其職的執行者
- **三道驗證閘**：CEO_Gate（人類批准）/ Stage Gate（PM closure）/ Mini Gate_Forward（per-task scoped）

設計目標：用 **PMP 紀律 + multi-agent verification** 結構，把「Claude 自說自話通過」這類 rubber-stamp 風險降到最低。

## 何時適合用

- 多步驟、跨領域的中大型開發任務（spec / dev / test / UX 都要動）
- 需要明確 audit trail、預算可追蹤、決策可回溯
- 有「中途想換方向」的可能 → 透過 CCB-Light/Heavy 走正式 change control

不適合：

- 單檔修改、trivial typo fix、純探索查詢 → 直接用 Claude Code 即可，這個 plugin 是 overkill

## 安裝

```bash
# 1. clone 到 Claude Code plugins 目錄
cd ~/.claude/plugins
git clone https://github.com/HsuTse/teamwork-leader.git

# 2. 在 ~/.claude/settings.json 啟用
# "enabledPlugins": [..., "teamwork-leader"]

# 3. 重啟 Claude Code session
```

啟用後即可在任何 session 使用 `/teamwork-leader` 啟動 TeamLead 角色。

## Quick Start

```text
/teamwork-leader 我要建一個小型筆記 app，含 markdown 編輯、tag、搜尋
```

TeamLead 會：

1. **Boot sequence** — 載入操作規則（Step 0 強制 Read SKILL.md / stage-runbook.md / dispatch-header.md）
2. **Discovery** — 問你三個問題（目標 / 成功標準 / constraint）
3. **Branch + Worktree check** — 偵測 staging/release 分支，提示風險
4. **TeamFormation** — 建議啟用哪些 PM（預設 PO+RD+QA，UX/Ad-hoc 視範圍）
5. **CEO_Gate_0** — 用 6 verbs（approve/revise_next/revise_charter/redirect/pause/abort）給你結構化 prompt
6. 批准後進入 **Stage 1 PLANNING → EXECUTING → GATING → AWAITING_CEO** 循環

每 stage 結束 TeamLead 會重新 dispatch 各 PM，依 [`stage-runbook.md`](./skills/teamwork-leader-workflow/references/stage-runbook.md) 的狀態機運作。

## 核心特色

### 三道驗證閘

| Gate | 範圍 | 觸發 | 主導者 |
|---|---|---|---|
| **CEO_Gate_N** | 整 stage | 每 stage 收尾 | CEO（人類）批准 |
| **Stage Gate** | PM 工作物 | PM dispatch 結束 | PM 自行 closure |
| **Mini Gate_Forward** | 單一 task 的 `artifacts_touched` | KMR per-task divergence proxy 觸發 | TeamLead 自決（per-instance） |

### 自動化驗證採樣

PM 回傳含結構化驗證 meta block，TeamLead 依下列訊號自動決定採樣深度：

- **每次 dispatch**：依 PM 自評與實際結果的 divergence 決定 Aligned / Watch / Escalate
- **跨 stage**：每 PM 維持 rolling 3-stage 信任分級（restricted / standard / trusted），搭配 anti-gaming 偵測
- **per-task**：必要時觸發 Mini Gate_Forward，僅檢核該 task 的工作物，不消耗 retry 額度

詳見 [`anti-rubber-stamp.md`](./skills/teamwork-leader-workflow/references/anti-rubber-stamp.md)（Rule 0 / 0.5 / 2）+ [`stage-runbook.md`](./skills/teamwork-leader-workflow/references/stage-runbook.md) §EXECUTING step 7a。

### 變更控制（CCB）

- **CCB-Light** — 範圍小、可逆的 knob 微調（threshold ±2、selector_score ±0.5）
- **CCB-Heavy** — formula 結構性改變、kill-switch 啟動、charter milestone 變動

詳見 [`pmp-ccb.md`](./skills/teamwork-leader-workflow/references/pmp-ccb.md)。

## 專案結構

```
teamwork-leader/
├── .claude-plugin/plugin.json     # plugin manifest
├── commands/teamwork-leader.md    # /teamwork-leader slash command
├── skills/teamwork-leader-workflow/
│   ├── SKILL.md                   # TeamLead 操作 skill
│   └── references/                # 11 個 reference 文件
│       ├── stage-runbook.md       # 狀態機（PLANNING→EXECUTING→GATING→AWAITING_CEO）
│       ├── dispatch-header.md     # PM dispatch / return contract
│       ├── anti-rubber-stamp.md   # Rule 0/0.5/2，trust_tier，anti-gaming
│       ├── three-gates.md         # CEO Gate / Stage Gate / Mini Gate
│       ├── progress-md-schema.md  # PROGRESS.md + audit-trail.jsonl 結構
│       ├── pmp-ccb.md             # CCB-Light/Heavy 觸發條件
│       ├── pmp-wbs.md             # rolling-wave WBS
│       ├── pmp-lessons-learned.md # ProjectClose lessons
│       ├── reuse-map.md           # 與 user rules / 其他 skill 的關係
│       ├── schema-migration.md    # PROGRESS.md schema 遷移
│       └── value-driven.md        # value criteria 驗證
├── agents/                        # 5 個 PM agent
│   ├── po-pm.md / rd-pm.md / qa-pm.md / ux-pm.md / ad-hoc-pm.md
├── templates/                     # 8 個輸出 template
│   ├── PROGRESS.md.tpl / budget-proposal.md.tpl / project-close.md.tpl
│   ├── ccb-light.md.tpl / ccb-heavy.md.tpl / ccb-log.md.tpl
│   ├── stage-report.md.tpl / tasks.md.tpl
├── scripts/gate-requirement-runner.sh  # Gate_Requirement helper
└── docs/
    ├── phase-3-dogfood.md         # Phase 3 dogfood 計畫
    └── specs/2026-05-01-teamwork-leader-design.md  # 設計 spec（rev v3）
```

## 配置（CEO_Gate_0 knobs）

在 BudgetProposal 階段，CEO 可調整以下 knob：

| Knob | 預設 | 說明 |
|---|---|---|
| `pms` | PO + RD + QA + UX | 啟用哪些 PM |
| `retry_cap_per_gate` | 2 | 每 gate 重試上限 |
| `retry_cap_per_step` | 1 | 每 step 重試上限 |
| `parallel_pm_limit` | 2（hard limit 4） | 平行 PM 上限 |
| `gate_requirement_mode` | final stage only | Gate_Requirement 觸發時機 |
| `milestones` | derived from stage decomposition | 每 stage 的 milestone 清單 |
| `verify_policy` | `default` | 採樣深度（`minimal-per-dispatch` / `default` / `broad`） |
| `trust_tier_mode` | `enabled` | trust_tier 信任分級啟用（disable 走 CCB-Heavy） |
| `kmr_mode` | `enabled` | per-task Mini Gate 啟用（disable 走 CCB-Heavy） |

完整 knob 表見 [`templates/budget-proposal.md.tpl`](./templates/budget-proposal.md.tpl)。

## 狀態與限制

**已知限制**：

- **尚未 dogfood**：所有驗證 threshold 皆為 seed values，待真實 project 校準
- **anti-gaming 觸發前提未驗證**：部分 anti-gaming trigger 依賴 PM 在實際 dispatch 中產生足夠 variance（見 [`docs/phase-3-dogfood.md`](./docs/phase-3-dogfood.md) §6）
- **CGR（Calibration Governance Review）deferred**：需 ≥3 stages clean dogfood data 後才評估

## 文件導引

從哪裡開始讀：

1. **使用者** → 直接跑 `/teamwork-leader` 試用，看 [`commands/teamwork-leader.md`](./commands/teamwork-leader.md) 了解 boot sequence
2. **想了解設計動機** → [`docs/specs/2026-05-01-teamwork-leader-design.md`](./docs/specs/2026-05-01-teamwork-leader-design.md)（1079 行完整 spec）
3. **想魔改 / 貢獻** → [`skills/teamwork-leader-workflow/SKILL.md`](./skills/teamwork-leader-workflow/SKILL.md) + 11 個 reference
4. **想理解三道 gate** → [`skills/teamwork-leader-workflow/references/three-gates.md`](./skills/teamwork-leader-workflow/references/three-gates.md)
5. **想用 anti-rubber-stamp 機制** → [`skills/teamwork-leader-workflow/references/anti-rubber-stamp.md`](./skills/teamwork-leader-workflow/references/anti-rubber-stamp.md)

## License

MIT — 見 [LICENSE](./LICENSE)。

## Acknowledgements

- 設計概念部分啟發自 KL-divergence-based triggering 與 capacity-saturation 原則
- 流程框架沿用 PMP（Project Management Professional）的 stage / gate / CCB / RAID / Lessons Learned 慣例
- 使用 Claude Code 的 plugin / skill / agent / command / hook 架構

## Roadmap

- [ ] 在真實 project 跑 dogfood，校準所有 seed thresholds
- [ ] 確認 `verification_self_redundancy` 在實際 PM dispatch 中有 variance（不是 constant emit）
- [ ] 收集 ≥3 stages clean data → 進 Phase 4 CGR（Calibration Governance Review）
- [ ] 視需要加入 PM-side adaptive verification depth（目前 sampling 全由 TeamLead 決定）
