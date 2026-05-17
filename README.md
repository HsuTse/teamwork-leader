# teamwork-leader

> 多 agent PMP 專案編排：TeamLead 統籌 PO/RD/QA/UX/Ad-hoc 角色 PM，透過 stage-gated 流程與三道驗證閘執行專案。

[![version](https://img.shields.io/badge/version-0.1.11-blue.svg)](./.claude-plugin/plugin.json)
[![license](https://img.shields.io/badge/license-MIT-green.svg)](./LICENSE)

各版本變更記錄見 [CHANGELOG.md](./CHANGELOG.md) 與 GitHub Releases。

---

## 這是什麼

`teamwork-leader` 是一個 [Claude Code](https://claude.com/claude-code) plugin，把單一 Claude session 變成一個小型專案組織：

| 角色 | 身分 | 職責 |
|---|---|---|
| **CEO** | 使用者 | 在 gate 給出 approve / revise / abort 等決策 |
| **TeamLead** | plugin 的 skill | 專案編排者 — 管理 stage、預算、RAID、CCB，不寫 code |
| **PMs** | 5 個 subagent | PO / RD / QA / UX / Ad-hoc，各司其職的執行者 |

設計目標：用 **PMP 紀律 + multi-agent verification** 結構，把「Claude 自說自話通過」這類 rubber-stamp 風險降到最低。

## 何時適合用

**適合** — 多步驟、跨領域的中大型開發任務（spec / dev / test / UX 都要動）；需要明確 audit trail、預算可追蹤、決策可回溯；中途可能換方向、需要正式 change control。

**不適合** — 單檔修改、trivial typo fix、純探索查詢。直接用 Claude Code 即可，這個 plugin 是 overkill。

## 安裝

透過 Claude Code plugin marketplace：

```bash
claude plugin marketplace add HsuTse/teamwork-leader   # 1. 註冊 marketplace
claude plugin install teamwork-leader@teamwork-leader  # 2. 安裝
# 3. 重啟 Claude Code session
```

- 更新：`claude plugin update teamwork-leader@teamwork-leader`
- 移除：`claude plugin uninstall teamwork-leader@teamwork-leader`

### 依賴

| 元件 | 需求 | 用於 |
|---|---|---|
| Claude Code | 支援 plugin / skill / agent / hook | 全部功能 |
| Python | ≥ 3.10 | hooks 與 auto-resume daemon |
| macOS launchd | macOS only | auto-resume daemon（其他平台自動降級，核心流程不受影響）|
| bash + `claude` CLI | — | Gate_Requirement runner |

核心 TeamLead 流程（skill / command / agents / templates）為純 Markdown，無執行期依賴；上述依賴僅 auto-resume daemon 等選用功能需要。

## 執行方式

```text
/teamwork-leader 我要建一個小型筆記 app，含 markdown 編輯、tag、搜尋
```

TeamLead 的 boot sequence：

1. **Boot** — 載入操作規則（強制 Read SKILL.md / stage-runbook.md / dispatch-header.md）
2. **Discovery** — 問三個問題（目標 / 成功標準 / constraint）
3. **Branch + Worktree check** — 偵測 staging/release 分支，提示風險
4. **TeamFormation** — 建議啟用哪些 PM（預設 PO+RD+QA，UX/Ad-hoc 視範圍）
5. **CEO_Gate_0** — 用 6 verbs（approve / revise_next / revise_charter / redirect / pause / abort）給結構化 prompt
6. 批准後進入 stage 循環

`/teamwork-leader` 不帶參數即為 **resume 模式** — 偵測既有 `PROGRESS.md`，比對狀態機與實際進度後接續。

## 架構

### 狀態機

每個 stage 依 [`stage-runbook.md`](./skills/teamwork-leader-workflow/references/stage-runbook.md) 走固定循環：

```
PLANNING → PLAN_AUDIT → EXECUTING → GATING → REPORTING → AWAITING_CEO
                                                              │
                          ESCALATED ◄── retry 耗盡 / INCONCLUSIVE
```

TeamLead 是 `PROGRESS.md` 狀態機欄位的唯一寫入者；PMs 以結構化 JSON payload 回報，由 TeamLead parse 後序列化。

### 專案結構

```
teamwork-leader/
├── .claude-plugin/plugin.json     # plugin manifest
├── commands/teamwork-leader.md    # /teamwork-leader slash command
├── skills/teamwork-leader-workflow/
│   ├── SKILL.md                   # TeamLead 操作 skill
│   └── references/                # 12 份 reference + discipline/ 子目錄
├── agents/                        # 5 個 PM agent（po/rd/qa/ux/ad-hoc）
├── templates/                     # 9 份輸出 template（PROGRESS / budget / CCB / stage-report …）
├── hooks/                         # PreCompact / SessionStart / Stop hook
├── lib/                           # baton-writer / gate-lock / handoff-builder / notifier
├── scripts/                       # daemon.py / install.py / gate-requirement-runner.sh
├── tools/                         # 量測與輔助腳本
└── docs/specs/                    # 設計 spec
```

## 方法論

流程框架沿用 **PMP（Project Management Professional）** 慣例，並疊加 multi-agent 驗證層：

- **Rolling-wave WBS** — stage 以 milestone 粒度規劃，當前 stage 細化到 task 粒度（[`pmp-wbs.md`](./skills/teamwork-leader-workflow/references/pmp-wbs.md)）
- **Stage Gate** — 每個 stage 收尾須通過驗證才前進，不可跳過
- **RAID Register** — Risk / Assumption / Issue / Dependency 持續追蹤於 `PROGRESS.md`
- **Change Control（CCB）** — 換方向走正式變更控制（見下）
- **Lessons Learned** — ProjectClose 收尾的回溯協定（[`pmp-lessons-learned.md`](./skills/teamwork-leader-workflow/references/pmp-lessons-learned.md)）

### 三道驗證閘

| Gate | 範圍 | 觸發 | 主導者 |
|---|---|---|---|
| **CEO_Gate** | 整個 stage | 每 stage 收尾 | CEO（人類）批准 |
| **Stage Gate** | PM 工作物 | PM dispatch 結束 | PM 自行 closure |
| **Mini Gate_Forward** | 單一 task 的工作物 | per-task divergence proxy 觸發 | TeamLead 自決 |

Gate 一律輸出結構化 classifier（`verdict` / `root_cause` / `evidence` / `dod_status`）；parse 失敗則 re-dispatch 一次，再失敗即 escalate CEO。詳見 [`three-gates.md`](./skills/teamwork-leader-workflow/references/three-gates.md)。

### Anti-rubber-stamp 驗證

PM 回報附結構化驗證 meta block，TeamLead 依訊號自動決定採樣深度：

- **每次 dispatch** — 依 PM 自評與實際結果的 divergence 分級 Aligned / Watch / Escalate
- **跨 stage** — 每 PM 維持 rolling 3-stage 信任分級（restricted / standard / trusted）+ anti-gaming 偵測
- **PLAN_AUDIT** — Opus 計劃審查者套用 Rule 7 anti-self-skip：禁止用 `"skip"` / `"none"` 等空值填 `suggested_fix` 來假性 rubber-stamp 計劃

詳見 [`anti-rubber-stamp.md`](./skills/teamwork-leader-workflow/references/anti-rubber-stamp.md) 與 [`plan-audit-rubric.md`](./skills/teamwork-leader-workflow/references/plan-audit-rubric.md)。

### 變更控制（CCB）

- **CCB-Light** — 範圍小、可逆的 knob 微調，session 內由 PO 更新 docs + ccb-log
- **CCB-Heavy** — formula 結構性改變、kill-switch、charter milestone 變動，須 CEO_Gate 批准

詳見 [`pmp-ccb.md`](./skills/teamwork-leader-workflow/references/pmp-ccb.md)。

## 核心功能

### Auto-Resume Daemon

Plugin 內建一個 macOS launchd daemon，補完 cross-session resume 的自動化路徑。Claude Code AutoCompact / `/clear` / 主動 pause 後，daemon 偵測 baton 狀態並自動 invoke `claude --resume`，免人工介入。安裝具 degraded-mode 容錯 — 在受限主機或非 macOS 環境會降級為手動模式並繼續，核心 TeamLead 流程不受影響。

### Dispatch schema validation

PM 回報的 mandatory fields 在寫入 audit-trail 前由 TeamLead parse-time validate；不完整則自動 re-dispatch 一次（獨立 retry pool），再失敗即 escalate。

### Role discipline references

`references/discipline/` 提供 6 份 portable 工作紀律（surgical-change / simplicity / typescript / testing / styling / mezzanine），作為各 PM 角色的紀律基線。專案自身的 `CLAUDE.md` 若有不同 convention，依 Claude Code 的 instruction precedence 自動優先。

## 配置（CEO_Gate_0 knobs）

BudgetProposal 階段，CEO 可調整：

| Knob | 預設 | 說明 |
|---|---|---|
| `pms` | PO + RD + QA + UX | 啟用哪些 PM |
| `retry_cap_per_gate` | 2 | 每 gate 重試上限 |
| `retry_cap_per_step` | 1 | 每 step 重試上限 |
| `parallel_pm_limit` | 2（hard limit 4） | 平行 PM 上限 |
| `gate_requirement_mode` | final stage only | Gate_Requirement 觸發時機 |
| `verify_policy` | `default` | 採樣深度（`minimal-per-dispatch` / `default` / `broad`） |
| `trust_tier_mode` | `enabled` | trust_tier 信任分級（disable 走 CCB-Heavy） |
| `kmr_mode` | `enabled` | per-task Mini Gate（disable 走 CCB-Heavy） |

完整 knob 表見 [`templates/budget-proposal.md.tpl`](./templates/budget-proposal.md.tpl)。

## 文件導引

| 想了解 | 從這裡開始 |
|---|---|
| 怎麼用 | 直接跑 `/teamwork-leader`；[`commands/teamwork-leader.md`](./commands/teamwork-leader.md) 看 boot sequence |
| 設計動機 | [`docs/specs/2026-05-01-teamwork-leader-design.md`](./docs/specs/2026-05-01-teamwork-leader-design.md) |
| 魔改 / 貢獻 | [`SKILL.md`](./skills/teamwork-leader-workflow/SKILL.md) + `references/` 各文件 |
| 版本變更 | [CHANGELOG.md](./CHANGELOG.md) |

## License

MIT — 見 [LICENSE](./LICENSE)。

## Acknowledgements

- 流程框架沿用 PMP（Project Management Professional）的 stage / gate / CCB / RAID / Lessons Learned 慣例
- 使用 Claude Code 的 plugin / skill / agent / command / hook 架構
