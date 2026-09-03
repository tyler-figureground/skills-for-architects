---
target: Atlas TUI
total_score: 20
max_score: 40
na_heuristics: 
p0_count: 0
p1_count: 3
timestamp: 2026-08-31T13-02-57Z
slug: tools-atlas-src-atlas-tui-app-py
---
## Design Health Score

| # | Heuristic | Score | Key issue |
|---|---|---:|---|
| 1 | Visibility of system status | 2/4 | No loading, progress, or durable operation result |
| 2 | Match system / real world | 2/4 | `DRIFT`, `STUB`, control plane, reloc, and sweep expose implementation language |
| 3 | User control and freedom | 2/4 | Cancel exists; undo, history, and reliable navigation do not |
| 4 | Consistency and standards | 2/4 | README says read-only while TUI mutates; unavailable actions remain global |
| 5 | Error prevention | 3/4 | Strong plans and safe core; forms permit invalid submission |
| 6 | Recognition rather than recall | 2/4 | Counts lack details, legend, and contextual actions |
| 7 | Flexibility and efficiency | 2/4 | Single-key actions; no filter, sort, batch, recents, or open-folder action |
| 8 | Aesthetic and minimalist design | 3/4 | Compact, but eight equal columns flatten hierarchy |
| 9 | Error recovery | 1/4 | Transient errors, unhandled I/O, conflict details discarded |
| 10 | Help and documentation | 1/4 | No contextual help, status glossary, or safety explanation |
| **Total** | | **20/40** | **Acceptable foundation; significant operational UX work needed** |

## Design Specificity Verdict

**Functionally specific, experientially generic.** Atlas models real studio-drive concepts well, but presents them as a generic table plus CRUD modals. The selected row should become a project health brief answering what is wrong, what Atlas can fix, and what requires review.

**Deterministic scan:** Impeccable detector found 0 mechanical issues in `tools/atlas/src/atlas/tui/app.py`. This is expected: its rules target common markup/CSS anti-patterns and do not measure TUI information architecture or operational safety.

**Visual evidence:** Representative Textual SVG at 130x36 rendered title, table, selection, and status summary. Browser overlay unavailable because the browser integration rejected the unconfigured temporary localhost origin.

## Overall Impression

Excellent safety core and clean foundation. Biggest opportunity: turn a passive conformance scoreboard into a fast, reassuring diagnose-preview-act workspace.

## What's Working

- **Safety-first core:** blessed folder choices, exact plans, confirmation, no-clobber behavior, and rmdir-only cleanup.
- **Portfolio pulse:** drive identity, map version, statuses, and summary support rapid triage.
- **Keyboard baseline:** direct keys, focused table, standard Textual controls, and live folder-name preview.

## Priority Issues

### [P1] Health table is a diagnostic dead end
- **Why it matters:** Counts identify risk but hide exact missing files, drift, relocations, sweeps, and unfiled items.
- **Fix:** Wide master-detail layout; narrow `Enter` drilldown. Show exact findings grouped as Atlas can fix, review required, and informational. Replace `?` with `UNFILED` or `REVIEW`.
- **Suggested command:** `/impeccable layout`

### [P1] Shared-drive work blocks without trustworthy recovery
- **Why it matters:** Synchronous scans can freeze the UI. Clean/conform I/O errors can escape. Conflict notes disappear.
- **Fix:** Textual thread workers, loading state, stale-result rejection, persistent prior inventory, retry, and durable per-action Done/Skipped/Conflict/Failed results.
- **Suggested command:** `/impeccable harden`

### [P1] Published safety posture contradicts the product
- **Why it matters:** `README.md` says P1 read-only while New, Add, Clean, and Conform mutate files. Trust and deployment risk.
- **Fix:** Reconcile release stage immediately. Add explicit Review-only versus Operate mode only if both are real product modes. Surface safety guarantees near mutation previews.
- **Suggested command:** `/impeccable clarify`

### [P2] Actions are global, terse, and context-insensitive
- **Why it matters:** Seven visible shortcuts create noise and silently no-op outside valid states.
- **Fix:** Focus-scoped bindings, `check_action`, `?` help panel, built-in command palette, disabled reasons, and reliable Esc hierarchy.
- **Suggested command:** `/impeccable distill`

### [P2] Portfolio-scale efficiency is missing
- **Why it matters:** Dozens of projects make row-by-row diagnosis slower than existing scripts.
- **Fix:** Stable project row keys, `/` substring filter, status filters, severity/name sorting, open-folder action, then marked-project batch plans only after single-project result UX is solid.
- **Suggested command:** `/impeccable shape`

## Persona Red Flags

- **Alex, power user:** no search, sort, filter, batch, recent projects, open folder, or CLI-equivalent conform-all path.
- **Jordan, first-timer:** unexplained `DRIFT`, `STUB`, `Reloc`, `Sweep`, blanks, and `?`; no route from count to cause; placeholder-only form labels.
- **Sam, keyboard/accessibility user:** keyboard baseline is promising, but modal Escape, focus order, announcements, long-plan review, and keyboard-only flows are untested. Textual screen-reader support remains unresolved, so CLI parity must remain the accessible fallback.

## Minor Observations

- Create remains enabled with empty project name.
- Add remains enabled with no selection.
- Add-folder options are flat rather than grouped by section.
- Summary omits total project count.
- Narrow-terminal behavior is undefined.
- TUI tests cover three happy paths only.
- Declared `textual>=0.80` conflicts with development on locked Textual 8.2.8; newer APIs require a raised minimum or compatibility tests.

## Questions to Consider

- Is Atlas primarily a drive-health dashboard, a mutation console, or an explicit two-mode product?
- Should Enter always answer “Why is this project not OK?” before mutation becomes available?
- What proof earns trust before Conform: exact paths, collision forecast, operation history, rollback, or some subset?
- Optimize first for an operations specialist managing 50 projects or a coordinator using Atlas twice monthly?
