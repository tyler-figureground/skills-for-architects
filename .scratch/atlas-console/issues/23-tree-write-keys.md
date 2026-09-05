---
title: "The tree's write keys, the inline confirm, and the undo stack"
date: 2026-09-04
generated_by: skills-for-architects
---

# The tree's write keys, the inline confirm, and the undo stack

Type: task
Status: open
Blocked by: -
Parent: ../map.md

## Question

The tree reads. It does not write. Ticket 22 built the widget over the seam ticket
07 settled, and ADR 0006's other half has never been built: **the repair keys on a
node, the inline confirm on the operation line, and the per-project undo stack.**

Core already has all of it. Ticket 21 built and tested `build_repair_plan`,
`invert_plan`, `Move` / `Action.moved`, and `Guard` at two scopes. This is TUI
work against a settled surface, plus the CLI form ADR 0008 now makes non-negotiable
in the same session.

Do, test-first:

- **A repair key on the selected node.** Drifted earns RENAME, Misplaced
  RELOCATE, Loose SWEEP. Unfiled earns nothing but reveal - it is the one state
  Atlas can never fix. Mapped earns nothing. One key, not four: the node's Filing
  State already decides which Action `build_repair_plan` slices out, so the key
  means "repair this" and the model picks the kind. A key that does nothing on the
  selected node must say so rather than being silently inert - ADR 0007's
  correction bites here, because **only control-plane Expectations are
  repairable** and conform has never created a mapped section.
- **The inline confirm.** ADR 0006: confirmation weight follows plan size. A
  one-Action Plan confirms **on the operation line**, not in a modal. Longer plans
  keep the modal that exists. The operation line is `#operation` and already has
  `-warning` and `-error` variants; a confirm is a third state, and it has to be
  legible in both Compositions and at 46 columns.
- **The scoped guard on apply.** Never `scan_drive`. `Guard.for_action` re-reads
  the map and re-enumerates the two folders the Action touches - 4.24 seconds
  becomes two enumerations. A stale guard refuses and says why.
- **The undo stack.** One per Project, in memory, no redo. Undo pops, inverts via
  `invert_plan`, and runs **the same scoped guard** on the way back - that is what
  lets the stack be optimistic rather than eagerly invalidated. `invert_plan`
  refuses a Plan holding a Backfill, a file-empty removal, or a Conflict; the key
  must present that refusal, not swallow it. Undo restores the precondition that
  offered the repair, so re-pressing the repair key **is** redo.
- **Reconcile after the write.** ADR 0007: forget the folders the Move Manifest
  names, take the fresh report, move the cursor to where the node went. Already
  decided; this is where it gets exercised for the first time.
- **Path length warns and obeys.** `build_plan` computes it; the confirm surfaces
  it; `long_path()` is never applied on the write side. A warning is only honest
  if Atlas cannot silently exceed 260.

## The CLI form this ticket owes

ADR 0008: a capability that writes owes a CLI form, discharged in the same session,
either order. `conform --project NAME --apply --only KIND` already exists and
covers the four action kinds. Two things are missing and both are this ticket's:

- **`conform --node PATH`** - target one node by Node Key rather than filtering by
  action class. `--only` filters by kind, which cannot express "this folder".
- **Undo.** Shape is open: `conform --undo` against a persisted manifest, or
  `--json` emitting the Move Manifest so a caller can invert it themselves. The
  TUI stack is in-memory and per-session; the CLI has no session, so this is a
  real design question and not a transcription. **Settle it before building it.**

## Why it is worth doing

It is the last thing between the tree and the map's destination sentence - "every
write still crossing an `atlas.core` plan with preview and confirmation". Every
piece it needs is built and tested. And it is the ticket that finally exercises
`invert_plan`, `Guard.for_action` and reconcile-by-manifest against a real widget
rather than against fixtures.

## Constraints

- ADR 0006 is the contract. Deviating from it is a decision and goes back on
  ticket 04.
- ADR 0008 is the parity rule. The CLI form ships this session.
- ADR 0007's correction stands: only control-plane Expectations are repairable.
- Fixture drives only. Never the studio drive.
- Colour from `tui/tokens.py`; the app CSS block is geometry only. The confirm
  state on the operation line is a token, not a hex.
- The confirm must read at 46 columns, and colour may not be the only thing
  distinguishing it from `-warning` and `-error` (ADR 0008).
