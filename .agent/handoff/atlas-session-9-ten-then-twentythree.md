---
title: "Atlas session 9: ticket 10, then ticket 23"
date: 2026-09-04
generated_by: skills-for-architects
---

# Atlas session 9: ticket 10, then ticket 23

Effort: `atlas-console`. Two tickets, in this order, on the user's instruction.

Baseline at start: **360 tests pass**, repo lint green, `main` clean and ahead of
`origin/main` by 26 commits, unpushed. `git fetch` run; behind 0.

## Why this order

Ticket 10 has slipped three sessions (6, 7, 8) and each one added surface that
inherits its unanswered question. Ticket 23 adds two more - a repair keybinding on
a node and an inline confirm on the operation line. Settling 10 first means 23
lands already conformant instead of adding a fourth session of debt.

## Phase plan

- [ ] **P0 - survey.** Read ticket 10, CONTEXT.md, the CLI surface and its
  `--json` contract, the TUI-only capabilities added in sessions 6-8, and the
  narrow-width render where colour carries Filing State alone.
- [ ] **P1 - ticket 10, grilled.** Resolve the five questions on the ticket. The
  live one is colour-carries-meaning at narrow widths. Output: Resolution section,
  map line, ADR if the decision earns one, CONTEXT.md vocabulary.
- [ ] **P2 - ticket 10, whatever it obliges.** Only if the decision requires code
  to stop the debt growing. Scope stated before starting.
- [ ] **P3 - ticket 23, charted.** The tree's writes. Repair keys on a node, the
  inline confirm on the operation line, the per-project undo stack. Write the
  ticket before building it.
- [ ] **P4 - ticket 23, built.** Test-first through `/tdd` against
  `build_repair_plan`, `invert_plan`, `Guard.for_action` - all built and tested in
  session 8.
- [ ] **P5 - verify and close.** Full suite, repo lint, headless render at the
  measured widths. Resolution sections, map lines, commits, wayfinder update.

## Constraints carried in

- ADR 0006 is ticket 23's contract; deviating is a decision and goes back on
  ticket 04.
- Fixture drives only. Never the studio drive, never a shared drive.
- Colour comes from `tui/tokens.py`; the app CSS block is geometry only.
- Verification widths are the measured ones: 179, 153, 120, 87, 77, 46 columns;
  51, 30, 24 rows.
- Tracker is local Markdown under `.scratch/atlas-console/issues/`. This repo has
  GitHub issues disabled.

## Log

<!-- appended per phase -->
