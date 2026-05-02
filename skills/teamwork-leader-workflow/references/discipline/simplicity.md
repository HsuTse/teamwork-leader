# Simplicity Discipline

Applicable to: **RD PM** (and any role making code edits)

## Core principle

只解 stated problem，不投機性增添。Single-use 程式碼不建立抽象。

## Rules

- 不加任何超出需求的 feature；只解 stated problem
- 不為 single-use 的程式碼建立抽象
- 不要主動加「彈性」或「可設定性」，除非需求明示
- 不要為不可能發生的情境寫 error handling
- 不要為 internal code 加 validation；只在 system boundaries（user input、external API）validate
- 信任 framework guarantees，不要重複 assertion
- 若寫到 200 行而 50 行就夠，立即改寫
- 自問：資深工程師會覺得這段過度設計嗎？若會，簡化

## Anti-patterns

- 加了 X 因為「未來可能需要」— YAGNI
- 「為了 testability」抽出 interface 但只有一個 implementation — 過度抽象
- 加 fallback / error handling 給「不可能發生的 case」— 防禦性過度
- 加 feature flag / 設定項給單一場景 — 配置性過度
- 寫 generic util 只因為「也許別處會用」— 投機抽象

## When in doubt

只寫 stated problem 解法。需要的彈性等到第二次 use case 出現再加（rule of three）。

## Override

User-level rules at `~/.claude/rules/CONTRIBUTING.md` (if present) take precedence per user-instruction priority. This file is plugin's portable default for users without that file.
