---
title: "The core write surface for the tree, as Atlas code"
date: 2026-09-03
generated_by: skills-for-architects
---

# The core write surface for the tree, as Atlas code

Type: task
Status: open
Blocked by: -
Parent: ../map.md

## Question

Ticket 04 decided the tree's write contract and ADR 0006 records it. None of it
exists in `atlas.core` yet.

Build the core side, ahead of and independent of the tree widget. Everything here
is testable without a TUI, and `conform` gains from it whether the tree ships or
not.

Do, test-first per the map's `/tdd` note:

- **`Action.moved`** - the move manifest. Every `(src, dst)` pair `_apply_move`
  actually moved, including inside a merge. Empty until applied. `_apply_sweep`
  and `_apply_backfill` fill it too, so a Plan is uniformly invertible or
  uniformly not.
- **A one-action plan builder.** `build_plan` currently takes a whole
  `ProjectReport`. The tree needs the Plan for one node's Repair - Drifted to
  RENAME, Misplaced to RELOCATE, Loose to SWEEP - and the Companion needs the Plan
  for one unmet Expectation as BACKFILL. Same `Action` values `build_plan` would
  have produced for the same node; a test should assert exactly that rather than
  trusting it.
- **The inverse plan.** Given an applied Plan, produce the Plan that reverses it
  from the manifests. Undo then flows through `apply_plan` like anything else.
- **The scoped guard.** Revalidate a one-action Plan by re-reading the drive map,
  re-enumerating the source's and destination's parents, and rebuilding the single
  Action. Same abort semantics as the full-rescan guard in `action_conform`. Both
  guards must produce the same verdict on the same divergence - worth a test that
  runs them side by side on a fixture drive.
- **Path-length warning on the Action.** Computed in `build_plan` at preview time:
  walk the source subtree once for its deepest relative path, add the destination
  prefix, warn above 260. Surfaces in `--json`. **`long_path()` is not applied on
  the write side** - the warning is only honest if Atlas cannot silently exceed the
  limit.

Explicitly not here: the undo stack itself, the inline confirm, and the keybindings.
Those are TUI and belong with ticket 20's shell or with the tree.

Verification: `cd tools/atlas && uv run pytest`, green, with new tests for each
bullet. Fixture drives only - never a shared drive. State what ran.

## Constraints already fixed

- ADR 0006 is the contract. Deviating is a decision, not an implementation detail,
  and belongs back on ticket 04.
- `Action` is frozen and read by `conform`, the CLI, and `--json`. Adding fields
  must not break the six existing consumers; the `Listing` change in ticket 16 is
  the precedent for how to widen a core record safely.
- `apply_plan` never clobbers. CONFLICT stays a real outcome, and a Plan
  containing one is not invertible.
- Ticket 13's ban on recursive counts stands. The path-length walk is per previewed
  action, never per render.
