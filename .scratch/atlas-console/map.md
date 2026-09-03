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

- **Textual token layer.** Once the visual world is locked, the palette, glyph
  vocabulary, and rule weights need to live in one place every screen reads -
  a Textual theme, a CSS variable block, or a Python token module. Which, and how
  the existing modal CSS migrates onto it. Ticket 05 constrains it: tree nodes take
  no CSS at all, so whatever this layer is, `render_label` has to be able to read
  it from Python. Blocked in practice by ticket 14, which names what it keys on.
- **ASCII header implementation.** The wordmark itself plus the responsive collapse
  rule, the narrow-terminal fallback, and where drive identity sits relative to it.
  Direction is now 3D extruded gradient lettering - see ticket 02 - so this also
  owns the glyph table, the extrusion compositor, and the per-cell ramp sampler as
  real Atlas code rather than throwaway prototype code.
- **How far the retro register travels.** If it stops at the wordmark, nothing else
  changes. If it does not, scanline dimming on table rows, selection glow, and neon
  pane rules all become design work. Ticket 02 question 3 decides which.
- **File-level action set.** Which actions the tree offers, what core plan each
  builds, and how each previews. Depends on the write contract.
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
