# Map: Atlas console

Label: wayfinder:map
Effort: atlas-console
Started: 2026-09-02

## Destination

A shipped, installed Atlas that a studio principal and occasional studio staff both
want to open: the SOLID+VOID identity present on screen, a navigable per-project
folder tree that shows what is filed and what the drive map expects but disk lacks,
the project dossier readable in-app, drive-wide search, and file-level actions - all
still crossing `atlas.core` plans with preview and confirmation before any write.

Done means running against the real ARCHITECTURE drive, tests green, docs current.
Not a spec, not a mockup.

## Notes

**This map carries execution.** It overrides Wayfinder's plan-don't-do default: a
ticket here may ship code, not only a decision. Ticket types still hold - a grilling
ticket resolves a question, a task ticket does work that unblocks one.

Domain: Python 3, Textual 8.2.8, `tools/atlas`. A self-contained uv project and the
one code exception to this repo's content-is-Markdown rule (ADR 0002). Not covered
by `scripts/lint.sh`.

Skills every session should consult:

- `/impeccable` - any visual or interaction work. Terminal is the medium, so its
  web-specific bans (self-hosted display faces, drawn SVG icon sets, box-shadow
  depth) do not transfer; its craft floor - contrast, spacing rhythm, real states,
  product language, one authored moment - does. Unicode glyphs *are* the icon
  system here and monospace is not a costume.
- `/tdd` - changes to `atlas.core`.
- `/grilling` and `/domain-modeling` - any decision ticket. New vocabulary lands in
  `/CONTEXT.md`.
- `/codebase-design` - seam design, especially the tree seam.

Standing constraints:

- Every mutation crosses a plan built in `atlas.core`, previewed, and confirmed.
  The TUI never writes directly. CLI and TUI share the plan.
- The drive map (`_tools/<drive>-map.json`) is the only folder-structure brain.
  Atlas hard-codes zero canonical folder names.
- Never touch a production or shared drive during development. Build synthetic
  fixture drives, as `tests/conftest.py` and the prior smoke run did.
- Tree work is built on a plain Textual `Tree`, never `DirectoryTree`. Labels are
  always `rich.text.Text`, never `str`, or folder names containing square brackets
  are silently mangled. Selection is re-resolved from Atlas's own key after every
  refresh, because Textual restores the cursor by line number. Per-node load
  workers are never `exclusive`. All four are measured findings from ticket 05.
- Verification per session: `cd tools/atlas && uv run pytest`, plus a headless
  Textual render at 132x38 and 80x24. State which ran.
- Google Drive File Stream latency is the performance reality, not local disk.
  Local timings are not a latency claim.

Continuity: `.agent/handoff/` per this repo's checkpoint rule.

## Decisions so far

<!-- one line per closed ticket: gist plus link -->

- Destination, tree model, operator, and capability scope settled at charting.
  Filesystem-mirror tree with a separate not-on-disk list; both operators served;
  dossier, search, and file actions in scope; portfolio dashboard out.
- [Land the outstanding Atlas working tree](issues/01-land-outstanding-working-tree.md)
  - landed as four commits, `c6d564a..7737de7`, tests and lint green before
  committing. `.agent/`, `.impeccable/`, and `.scratch/` are tracked, not ignored.
  Not pushed.
- [Lock the Atlas visual world](issues/02-lock-the-visual-world.md) - POCHE world
  with an EMBER wordmark, rendered in half-blocks so the header costs 6 rows
  instead of 9 while the gradient gets finer. Collapse rule: full mark at >= 115
  columns, compact at 82 - 114, single bar below 82. Retro register stops at the
  wordmark and the cursor - no scanlines on data. Field muted, selected row the
  only full-strength thing on screen. `SETUP` moved from steel blue into the ember
  family. Prototype token values recorded on the ticket.
- [The wordmark and header, as Atlas code](issues/17-wordmark-and-header-in-atlas.md)
  - **shipped.** Half-block compositor, extrusion, ramp sampler and the three
  compositions, written fresh under test. Measured at 111 / 78 / 20 columns and
  4 / 4 / 1 rows. The width rule needed a correction the prototype hid: thresholds
  are the mark width plus the console's four columns of padding, which is exactly
  the published 115 and 82, and a test walks every width from 20 to 240 asserting
  the chosen composition fits. Replaces Textual's `Header`, refreshed on resize.
- [The token layer](issues/18-token-layer.md) - **built.** A Python module owns
  the palette and glyph table and generates the Textual CSS from it, because tree
  nodes take no CSS and `render_label` must read from Python. `MODAL_CSS` and
  `STATUS_STYLES` migrated; the app's CSS block is geometry only. Colour is tested
  by structure and contrast, never by hex literal - every text token must clear
  4.5:1, and the generated CSS is scanned so a hand-edited colour fails the suite.
  Tuning to pass that floor lightened four tokens. Flips ACTION to vermilion and
  REVIEW to ochre from the old yellow/red.
- [Do folders show a count, and of what](issues/13-folder-counts.md) -
  immediate-child counts only, folders and files counted separately, rendered only
  on Read folders and never as a zero on an Unread one. Recursive counts are out:
  they are a walk, and they are incompatible with lazy loading regardless of cost.
  Uncovered a live collision - `clean` removes folders with no file *anywhere
  beneath* while the tree calls a folder empty when it has no children *of its
  own*. Now named separately as **Fileless** and **Empty Folder** in `/CONTEXT.md`.
- [Enumeration failure as a core fact](issues/16-enumeration-error-as-a-core-fact.md)
  and [Extended-length paths](issues/19-extended-length-paths.md) - **built, not
  just decided.** `list_entries` returns a `Listing` carrying Load State; it
  iterates like the tuple it replaced so all six consumers were untouched, and is
  unconditionally truthy so `if listing:` cannot silently regress. `long_path()`
  applies the `\\?\` prefix on demand at the three read chokepoints. An
  unreadable project root is recorded, reported as REVIEW rather than READY or
  SETUP, and shown in its own detail block. `--json` gains `unreadable`. 211 tests
  pass; both live over-MAX_PATH folders verified fixed on the real drive.
- [Node kind vocabulary](issues/14-node-kind-vocabulary.md) - a node is a thing
  that exists on disk; an unmet map Expectation is not a node and is listed beside
  the tree, which means the prototype renders showing missing folders inline were
  wrong and the renderer drops those rows. Every node carries two orthogonal
  values: **Filing State** (Mapped / Drifted / Misplaced / Loose / Unfiled, first
  matching map rule wins) and **Load State** (Unread / Read / Unreadable /
  Partial). Emptiness is derived, never stored. Solid vs hatched answers "is
  anything wrong", colour answers "mine or Atlas's". Terms in `/CONTEXT.md`,
  decision in `docs/adr/0004`.
- [A latency number for the tree](issues/12-latency-budget.md) - measured on the
  live drive with the user's authorisation, read-only. The **whole studio drive is
  7,956 folders and 18,536 files, walked in 4.24 seconds**, so throughput is a
  non-issue at this size and a drive-wide index is affordable. The cost is all in
  the tail: cold p99 91 ms, worst 314 ms, nothing over a second. Budgets set -
  loading state at 120 ms, prefetch one level capped at 50, concurrency cap 4,
  count cap 500, cache TTL 60 s. Found two live `MAX_PATH` failures, one of which
  Atlas reports as an empty folder that is not empty. Report:
  `docs/research/atlas-drive-latency-measurement.md`.
- [Textual 8.2.8 tree widgets and lazy loading](issues/05-research-textual-tree-widgets.md)
  - build on plain `Tree`; `DirectoryTree` destroys injected nodes on reload, can
  only subtract paths, and costs ~2 stats per entry. Copy its lazy-load machinery,
  do not inherit it. Scrolling is virtualized but `_build()` is linear in expanded
  nodes - 20-30ms at 5000. Two measured silent-corruption traps: markup injection
  via `str` labels, and cursor restore by line number. Report:
  `docs/research/atlas-tree-widget-evidence.md`.
- [Reading a project tree over Google Drive File Stream](issues/06-research-drive-tree-cost.md)
  - shared drives are streaming-only; enumeration is the unit of cost, not `stat`;
  no official latency figure exists from anyone; recursive counts have no cheap
  primitive; stock Textual `DirectoryTree` is the wrong loader; filesystem watching
  is not a dependable staleness signal; `Path.rglob` swallows every `OSError` and
  must never be used here. Report: `docs/research/atlas-drive-tree-read-cost.md`.

## Not yet specified

Fog toward the destination. Graduates into tickets as the frontier clears it.

- **File-level action set.** Which actions the tree offers, what core plan each
  builds, and how each previews. Depends on the write contract.
- **Selection and focus rendering everywhere else.** Ticket 02 settled the cursor
  for the project list and the tree. Modals, the filter input, the command palette,
  and the search overlay all still show default Textual focus, which no longer
  matches. Small, and easy to forget until it looks wrong.
- **Long paths on the write side.** Reads are fixed; `conform` and `ops` are not.
  A move can push a path past MAX_PATH even when both endpoints were fine, and
  Atlas must not create a path Explorer, Revit and the PowerShell tools cannot
  open. Wants a length check in plan-building that refuses or warns, not a blind
  prefix. Possibly also a `doctor` finding for over-long paths, which was
  considered and deferred as a new finding type.
- **Deep unreadable detection.** `doctor` checks the project root only, because
  that is all `scan_drive` enumerates. A folder three levels down that cannot be
  read is invisible until the tree lands. Ticket 07 inherits it.
- **Tree states.** Loading, empty project, permission error, a folder too large to
  walk, a stale tree after an external change. Ticket 06 adds two that must be
  designed distinctly: **enumeration error**, which must never look like empty, and
  **truncated or partial**, because a count cap can be hit and because CPython
  issue 102993 shows `os.listdir` returning a partial result on a synced mount
  while Explorer reads it fine.
- **80x24 composition.** What the console becomes when neither pane fits.
- **Test strategy for the new surface.** The current three-happy-path TUI coverage
  will not hold a tree, a search overlay, and a dossier panel. Ticket 05 shows the
  shape that works: probe scripts driving real widgets through `App.run_test()`
  against the pinned venv, asserting on measured syscall and message counts rather
  than on rendered output.
- **Rebuild cost at depth.** `Tree._build()` is linear in expanded nodes and calls
  `render_label` once per line, and it fires on any mutation, resize or style
  change. Ticket 05 measured 20-30ms at 5000 expanded nodes and cut the median from
  25.4ms to 6.4ms by overriding `get_label_width`. Whether Atlas needs that, and
  what caps expansion depth, is unspecified.
- **Docs and release.** README, CHANGELOG, any ADR the seam decisions earn, and the
  `uv tool install --editable` redeploy.
- **Cache and invalidation layer.** Ticket 06 prescribes TTL plus explicit refresh
  plus subtree invalidation on Atlas's own mutations, in the shape rclone uses.
  Where that layer lives, what it keys on, and how conform and clean signal it.

## Out of scope

- **Portfolio dashboard.** A drive-wide home screen with health rollup, recent
  activity, and staleness. Ruled out at charting: the project list stays the
  landing surface.
- **Template copying.** Revit, Word, and spreadsheet template population at project
  creation. Already deferred by the intake work and not revisited here.
