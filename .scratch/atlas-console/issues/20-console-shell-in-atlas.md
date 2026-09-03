---
title: "The console shell, as Atlas code"
date: 2026-09-03
generated_by: skills-for-architects
---

# The console shell, as Atlas code

Type: task
Status: open
Blocked by: -
Parent: ../map.md

## Question

Ticket 03 decided the console's Regions, Compositions, breakpoints, keys, and
first paint. ADR 0005 records it. Nothing of it exists in `tools/atlas` yet:
`compose()` is still mark, drives, filter, `#workspace` as a flat `Horizontal` of
`#projects` and `#detail`, summary, operation, footer.

Build the shell, with the Tree Region and the Companion Region holding
placeholders. This is deliberately the frame without the tree - ticket 07 fills
the Tree Region, ticket 09 fills the dossier Companion Mode. Building them in that
order means the tree lands into a layout that already works, at every width,
rather than into one being invented around it.

Do:

- Three Regions and the Workspace container, per ADR 0005. `#detail` is replaced,
  not kept alongside.
- `HORIZONTAL_BREAKPOINTS` at 100 and 40, with Single-Region Composition below
  100 and the too-narrow line below 40. Vertical rules at 30 rows (merge summary
  and operation) and 16 rows (refuse).
- Collapse: `[`, `]`, `z`, with an explicit collapse outranking the breakpoint
  default and sticky for the session.
- Navigation: Enter drills, Escape unwinds, Tab moves to the next Region, `/`
  filters the focused Region. Identical semantics in both Compositions.
- `action_inspect` stops pushing `ResultModal`; project health becomes a Companion
  Mode, `d` cycles the modes, and the Companion snaps back to unmet Expectations
  when the Selected Project changes.
- Workspace title carrying the Project Name, permanently.
- Cursor-follow: debounced at ~150 ms, cache hits exempt. With no tree yet the
  placeholder can still exercise the debounce and the cancellation path.
- Context-sensitive summary line.
- Footer at 46 columns shows `?`, `Tab`, `Enter`.

Verification, per the map's constraint as ticket 03 revised it: headless renders
at the measured widths - 179, 153, 120, 87, 77, 46 - and at 51, 30, and 24 rows.
`uv run pytest` green. State which ran.

## Constraints already fixed

- ADR 0005 is the contract. Deviating from it is a decision, not an
  implementation detail, and belongs back on ticket 03.
- Colour comes from `tui/tokens.py`, never a hex literal; the app's CSS block is
  geometry only. The contrast test in the token suite must stay green.
- The wordmark's own thresholds (115 / 82) are independent of the layout
  breakpoints (100 / 40) and stay independent. Do not unify them.
- Textual-side traps from ticket 05 apply to anything tree-shaped built here.
