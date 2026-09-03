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

## Not yet specified

Fog toward the destination. Graduates into tickets as the frontier clears it.

- **Textual token layer.** Once the visual world is locked, the palette, glyph
  vocabulary, and rule weights need to live in one place every screen reads -
  a Textual theme, a CSS variable block, or a Python token module. Which, and how
  the existing modal CSS migrates onto it.
- **ASCII header implementation.** The wordmark itself plus the responsive collapse
  rule, the narrow-terminal fallback, and where drive identity sits relative to it.
- **File-level action set.** Which actions the tree offers, what core plan each
  builds, and how each previews. Depends on the write contract.
- **Tree states.** Loading, empty project, permission error, a folder too large to
  walk, a stale tree after an external change.
- **80x24 composition.** What the console becomes when neither pane fits.
- **Test strategy for the new surface.** The current three-happy-path TUI coverage
  will not hold a tree, a search overlay, and a dossier panel.
- **Docs and release.** README, CHANGELOG, any ADR the seam decisions earn, and the
  `uv tool install --editable` redeploy.

## Out of scope

- **Portfolio dashboard.** A drive-wide home screen with health rollup, recent
  activity, and staleness. Ruled out at charting: the project list stays the
  landing surface.
- **Template copying.** Revit, Word, and spreadsheet template population at project
  creation. Already deferred by the intake work and not revisited here.
