# CHANGELOG conventions

This repo's `CHANGELOG.md` loosely follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) with a few project-specific patterns.

## Per-version entry structure

Each `## [X.Y.Z]` entry uses a subset of these subsections (only include sections with actual content):

- `### Added` — new features / files / capabilities
- `### Changed` — modifications to existing behavior, bumped configs, renamed surfaces
- `### Fixed` — bug fixes (use over `Changed` when the prior behavior was clearly broken)
- `### Why` — project-specific extension: rationale paragraph for the release (not in upstream Keep-a-Changelog spec)
- `### Migration` — project-specific extension: upgrade-path guidance, breaking-change handling

## Forward-going convention: `### Notes` (plural), not `### Note:`

Historical `[0.1.7]` and `[0.1.8]` entries use `### Note: <one-off topic>` subsection headings to disclose specific edge cases (e.g., `[0.1.8] ### Note: [0.1.7] CHANGELOG entry not back-filled`). This deviates from the established Added/Changed/Why/Migration schema and was flagged by `/opus-review` and `/simplify` reviewers as schema drift.

**Forward-going convention** (applies to new `[X.Y.Z]` entries from v0.1.9 onward):

- **Preferred**: use `### Notes` (plural) for a free-form notes subsection containing 1+ bullet points of one-off disclosures. Place after `### Migration` if both exist.
- **Alternative for single one-off**: inline the disclosure within `### Why` as a parenthetical or final paragraph.
- **Avoid**: `### Note: <topic>` (colon + topic suffix) — looks like a heading-of-a-heading and confuses scanners that expect Keep-a-Changelog standard subsection names.

Historical `[0.1.7]` and `[0.1.8]` entries are NOT retroactively rewritten — they stand as-shipped. This convention applies only to entries authored after this document was added.

### Examples

**Good (plural `### Notes`)**:

```markdown
### Notes

- Skip-version 0.1.6 → 0.1.8 was intentional (charter freeze on 0.1.7 mid-flight; see PROGRESS.md for context).
- v0.1.7 CHANGELOG back-fill is a separate optional follow-up, not blocking this release.
```

**Good (inline within `### Why`)**:

```markdown
### Why

This patch corrects the calibration data drift between lessons-learned.v0.1.8.md and PROGRESS.md §Self-Audit (the canonical record showed 137 kT / 2 KMR fires; lessons-learned was claiming 98 kT / 1 KMR fire). No behavioral changes. (Note: the original drift originated in a "clean rewrite" that landed on the wrong number — preserved in commit message for traceability.)
```

**Discouraged (project-specific `### Note: <topic>`)**:

```markdown
### Note: prior version back-fill not done in this release

<paragraph>
```

## Version cadence

- **Patch (0.0.X)** — internal corrections, no user-visible behavior change
- **Minor (0.X.0)** — new features, additive amendments to FROZEN specs, codification work
- **Major (X.0.0)** — breaking changes (none planned for v0.X line)

## Entry ordering

Newest first. The `## [unreleased]` section, if present, lives above the highest `[X.Y.Z]` heading and is folded into a release entry at tag-time.

---

**Origin**: this convention document was created by the post-v0.1.8 cleanup batch (`chore/cleanup-batch-1-codification`) to formalize the `### Notes` vs `### Note:` decision flagged by `/simplify` Agent 3. See PROGRESS.md and `docs/archives/lessons-learned.v0.1.8.md` for the full audit trail.
