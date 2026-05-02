# TypeScript Discipline

Applicable to: **RD PM** (TypeScript projects only)

## Hard rules

- 禁止使用 `any`（包括 `as any`）
- 每個 function 都應宣告 return type（特別是 exported function）
- 可行時優先使用 `const`、`readonly` 與 immutable 寫法
- 避免不必要的 mutation
- 遵循專案既有 eslint / tsconfig 規則

## Common anti-patterns

| Pattern | Replacement |
|---|---|
| `as any` to silence type error | 釐清型別錯誤的真正原因；改寫程式碼或補正 type definition |
| Missing return type on exported function | 顯式宣告 `: ReturnType` |
| `let` for value never reassigned | 改 `const` |
| Mutating array/object in place | 改 immutable update（spread、map、filter） |
| Type assertion 大量出現 | 多半 design 問題；考慮重 design type relationship |

## When type error blocks dispatch

不要用 `as any` 繞過。流程：

1. 讀型別錯誤訊息，理解真正的型別不一致
2. 若是程式邏輯錯 → 改邏輯
3. 若是 type definition 不準 → 補 type
4. 若是上游 library 型別錯（rare）→ 在 return contract `raid_updates` 開 RAID-I 描述狀況；不繞過

## Override

User-level rules at `~/.claude/rules/CONTRIBUTING.md` (if present) take precedence per user-instruction priority. This file is plugin's portable default for users without that file.
