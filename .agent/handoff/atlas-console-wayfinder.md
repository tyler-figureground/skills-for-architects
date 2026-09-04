---
title: "Atlas console redesign - wayfinder continuity"
date: 2026-09-03
generated_by: skills-for-architects
---

# Atlas console redesign - wayfinder continuity

Status: layout and write contract settled; nothing is blocked; the tree is what remains
Date: 2026-09-03
Effort: `atlas-console`

## Where the work lives

The map is the canonical artifact, not this file.

- Map: `.scratch/atlas-console/map.md`
- Tickets: `.scratch/atlas-console/issues/NN-*.md`
- Tracker convention: local Markdown (`~/.claude/skills-archive-2026-07-21/setup-matt-pocock-skills/issue-tracker-local.md`), because no issue tracker was provisioned for this repo.

## Destination

A shipped, installed Atlas carrying the SOLID+VOID identity, a navigable per-project
folder tree with not-on-disk awareness, the dossier readable in-app, drive-wide
search, and file-level actions - every write still crossing an `atlas.core` plan with
preview and confirmation.

This map carries execution, not only decisions. That is a deliberate override of
Wayfinder's plan-don't-do default and is recorded in the map's Notes.

## Settled at charting

- Destination: a working app, not a spec.
- Tree model: filesystem mirror, with a separate not-on-disk list rather than ghost
  nodes merged inline.
- Operator: the principal daily and studio staff occasionally - both served, via
  progressive disclosure.
- In scope: dossier in-app, global search, file-level actions.
- Out of scope: portfolio dashboard.

## Session 1 output

- Rendered the current TUI headless for a baseline.
- Built three visual worlds as real Textual renders at 132x38 - POCHE, TITLE BLOCK,
  PAPER - and published them for comparison:
  https://claude.ai/code/artifact/4a9756ec-d166-44d0-b76d-ddd9979fbbc6
  Prototype source is throwaway and lives only in the session scratchpad. It is not
  Atlas code and must not become Atlas code.
- Charted the map with ten tickets and the fog.
- Dispatched research tickets 05 and 06 to parallel `/research` subagents. Both were
  instructed to write under `docs/research/`, create no branch, commit nothing, and
  never touch a production or shared drive.

## Session 2

- Landed the whole working tree on the user's instruction. Tests (201) and lint
  green before committing. `main` ahead of `origin/main`, not pushed.
- Visual world locked: **A - POCHE**. The user then reopened the wordmark itself,
  asking for retro-cyberpunk 3D extruded gradient lettering. Five treatments built
  and published on the same artifact; ticket 02 stays claimed on three questions.
- Both research tickets resolved and indexed. Six tickets graduated from what they
  surfaced: 11, 12, 13 from the Drive cost research; 14, 15, 16 from the Textual
  research.

## Session 3

Ticket 02 resolved: POCHE world, EMBER wordmark, half-block rendering. Header
went from 9 rows to 6 with a finer gradient, not a coarser one. Three-step
collapse rule by terminal width. Retro register stops at the wordmark and the
cursor. Tickets 17 (header as Atlas code) and 18 (token layer) graduated.

## Session 4

- Ticket 12 resolved by measurement. The user authorised reading the studio drive,
  read-only, nothing created. **The whole drive is 7,956 folders and 18,536 files
  and walks in 4.24 seconds.** Throughput is a non-issue at this size; the cost is
  all in the tail, cold p99 91 ms and worst 314 ms.
- That walk found **two live MAX_PATH failures**, one of which Atlas reports as an
  empty folder that contains an entry. Ticket 16 confirmed on production data;
  ticket 19 opened for the extended-length prefix decision. `find_empty_dirs` is
  verified not at risk - `os.walk` omits the failing directory, so neither it nor
  its parent is ever marked empty. False reporting, not destruction.
- Ticket 14 resolved. Two orthogonal axes - Filing State and Load State - rather
  than one flat enum. Unmet map Expectations are not nodes. Terms in `CONTEXT.md`,
  decision in `docs/adr/0004`.

## Known contradiction to fix

The published prototype renders draw missing folders **inline** in the tree as dim
hatched rows *and* list them under NOT ON DISK. That is the same fact twice and it
violates the filesystem-mirror model chosen at charting. Ticket 14 rules the inline
rows out. Whoever builds the renderer drops them; the NOT ON DISK list stays. The
sheet has not been re-rendered to match.

## Session 5 - first code

Tickets 16 and 19 built, not just decided. `list_entries` returns a `Listing`
carrying Load State; `long_path()` applies the `\?\` prefix on demand at the
three read chokepoints. 211 tests pass, up from 201. Both live over-MAX_PATH
folders verified fixed on the real drive; the one holding an item no longer
reports as empty.

Writes were deliberately left alone - a move can push a path past the limit, and
Atlas must not create paths Explorer and Revit cannot open. That check is in the
fog, owned by the conform work.

## Session 6 - the header is real

Tickets 13, 17 and 18 done. 261 tests pass, up from 211 at the start of the day.

- **Token layer** (`tui/tokens.py`). Python owns the palette and glyph table and
  generates the Textual CSS; `MODAL_CSS` and `STATUS_STYLES` migrated. Colour is
  tested by contrast and structure, never hex. That test failed on four of the
  prototype's tokens and they were lightened until it passed. It also flips ACTION
  to vermilion and REVIEW to ochre from the old yellow/red.
- **Wordmark** (`tui/wordmark.py`). Half-block compositor, extrusion, ramp sampler
  and three compositions, replacing Textual's `Header`. 111 / 78 / 20 columns and
  4 / 4 / 1 rows.
- **Counts.** Immediate children only, and only on a folder Atlas has actually
  read. Recursive counts are out - incompatible with lazy loading regardless of
  cost.

Two corrections worth carrying forward, both caught by building rather than
designing:

- The published width rule (115 / 82) is the mark widths (111 / 78) **plus the
  console's four columns of padding**. A naive "widest that fits" renders the mark
  flush against both edges. `MARGIN` is now a named constant.
- `ops.find_empty_dirs` removes folders with no file *anywhere beneath*, while the
  tree calls a folder empty when it has no children *of its own*. Two predicates,
  one word, and one of them deletes. Now named **Fileless** and **Empty Folder** in
  `CONTEXT.md`.

---
title: "handoff-tail.md"
date: 2026-09-03
generated_by: skills-for-architects
---

## Session 7 - the console has a shape

Ticket 03 resolved. No code this session: 03 is a grilling ticket and Wayfinder
allows one ticket per session. 261 tests still pass, lint green, nothing in
`tools/atlas` changed.

**The session's real find was a measurement, not a decision.** The effort had been
designing against 132x38 with 80x24 as the floor. Both were assumed and both are
wrong. Herdr - the agent runtime now in daily use - logs every PTY resize to
`~/AppData/Roaming/herdr/herdr-server.log`. Forty events on this machine:

- Columns: 46 (9), 77 (8), 153 (7), 179 (3), 87/88 (3), 120 (2), then 80, 57, 48, 39.
- Rows: 51 in 33 of 40 events, 52 in 3, then 40, 30, 24 once each.

Rows are abundant and near-constant. Columns are scarce and trimodal. **Eight of
the twelve distinct widths cannot hold two columns of content**, so the narrow
arrangement is the common case, not the fallback. The map's verification-sizes
constraint has been rewritten to the measured widths.

The decision that follows from it: three **Regions** - Project List, Tree Region,
Companion Region - in two **Compositions**. The Companion sits *under* the Tree,
not beside it, spending rows to save columns. Split Composition at >= 100 columns,
Single-Region below, refusal under 40 columns or 16 rows. Navigation is identical
in both. Explicit collapse outranks the breakpoint default. The Workspace follows
the list cursor, debounced 150 ms with cache hits exempt, so the tree is populated
at first paint rather than on a keystroke.

Two things get absorbed rather than added: `#detail` and `action_inspect`'s health
modal both become Companion Modes. That reclaims Enter, which the tree needs.

Recorded in `docs/adr/0005`, vocabulary in `CONTEXT.md` under Atlas Console
Layout. Ticket 20 graduated - the console shell as Atlas code, the frame without
the tree in it.

---
title: "handoff-tail-2.md"
date: 2026-09-03
generated_by: skills-for-architects
---

## Session 7 continued - the write contract

Ticket 04 resolved in the same session as 03, on the user's instruction to
proceed. Wayfinder's one-ticket-per-session rule was set aside deliberately, not
forgotten; context budget was the reason for it and there was budget.

Reading the write path first changed the ticket. Two findings the ticket's own
framing had wrong:

- **The staleness guard is a full `scan_drive`.** `action_conform` rescans the
  entire drive on confirm - 4.24 seconds per ticket 12 - and refuses to write
  unless the map, the rebuilt plan, and `_project_token` all match the preview.
  Correct once for a deliberate conform. Fatal per keystroke on a node.
- **`_project_token` only covers the project root** (`app.py:73`, the sorted
  `(name, is_dir)` list of `root_entries`). A node three levels down was never
  covered by the guard the ticket assumed protected it.

The decision, in one line: **the tree invents no new action kinds.** Drifted,
Misplaced and Loose are exactly RENAME, RELOCATE and SWEEP; an unmet Expectation
is BACKFILL and belongs to the Companion because ADR 0004 says it is not a node.
Core gains a way to build a one-Action Plan, nothing more.

Everything else follows from that plus the user's two overrides - full undo stack
rather than the one-level version recommended, and warn rather than refuse on
MAX_PATH:

- Confirmation weight follows plan size. One action confirms inline on the
  operation line; longer plans keep the modal.
- Full undo stack, **one per Project**, in memory, no redo. Undo restores the
  precondition that offered the action, so re-pressing the repair key is redo.
- `Action.moved`, a manifest of what each apply actually moved. A merge cannot be
  inverted without it, and inverting by inference is data loss.
- Revalidation scopes to the action. Same guard runs on undo pops, which is what
  lets the stack be optimistic rather than eagerly invalidated.
- Path length warns in `build_plan`, and **`long_path()` is never applied on the
  write side** - the warning is only honest if Atlas cannot silently exceed 260.

Recorded in `docs/adr/0006`, vocabulary in `CONTEXT.md` under Atlas Writes. Ticket
21 graduated - the core write surface, buildable and testable without a TUI. The
write-side MAX_PATH fog patch is cleared; what is left of it is a narrower `doctor`
question, still deferred.

## Frontier

Unblocked and unclaimed: 08, 09, 10, 11, and the tree widget, which is not yet a
ticket.
Blocked: none.
Resolved: 01, 02, 03, 04, 05, 06, 07, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21.

**Nothing is blocked any more.** Every remaining ticket is takeable.

**The tree widget is the obvious next thing and it has no ticket.** Ticket 07
settled the seam and ticket 20 built the frame it lands in, so what remains is a
plain Textual `Tree` over `core.tree`: `render_label` with `rich.text.Text` (never
`str` - ticket 05's latent markup bug), per-node workers that must not be
`exclusive`, lazy expansion off `children()`, and cursor restore by Node Key with
`call_after_refresh`. Every trap is already written down on ticket 05. Chart it
before building it.

Two build tickets are ready and independent of each other:

- **21, the core write surface.** Test-first, no TUI, fixture drives only.
  `conform` gets better whether the tree ships or not. The lowest-risk next
  session.
- **20, the console shell.** The frame from ADR 0005 with placeholders in the Tree
  and Companion Regions, so the tree later lands into a layout that already works
  at every width.

**07 is the seam** and is the largest remaining decision. It is unblocked now but
reads better after 21 exists, because 21 settles what core actually hands over.

**10 is the one that keeps slipping.** Sessions 6 and 7 each added surface that
inherits the unanswered accessibility question - a wordmark, five keybindings,
three Regions, two Compositions, and now an undo stack and an inline confirm on
the operation line. It has been recommended forward twice and taken neither time.

## Session 8 - four tickets, test-first

21, 07, 15 and 20 in that order, driven through `/tdd`. 339 tests pass, up from
261 at the start of the day. Repo lint green throughout. Continuity for the run is
in `.agent/handoff/atlas-tdd-four-tickets.md`.

- **21, the core write surface.** `Move` and `Action.moved` give every applied
  action a manifest; `build_repair_plan` slices one Action out of the Plan conform
  already builds; `invert_plan` reverses it from manifests and refuses outright
  when a Backfill, a file-empty removal, or a Conflict leaves nothing to reverse.
  `Guard` now exists at two scopes with three tests running them side by side.
  Path length warns from `build_plan`; `long_path()` is still absent from every
  write path.
- **07 and 15, the seam and its aftermath.** A lazily-expanding handle,
  `core.tree`. Below the root, where `report_project` has no opinion, containment
  decides Filing State. The Node Key is the project-relative path. After a write
  the tree reconciles by Move Manifest - the same two folders the scoped guard
  watched - and the cursor follows what it repaired. ADR 0007.
- **20, the console shell.** Layout rules as a pure module, `tui/layout.py`, with
  `app.py` applying them. Three Regions, two Compositions, collapse, navigation,
  Companion Modes, narrow chrome. The health modal is gone and Enter is reclaimed.

Two corrections found by building rather than deciding:

- **Only control-plane Expectations are repairable.** ADR 0006 said an unmet
  Expectation is a Backfill. Conform has never created a mapped section and would
  report an unknown item and skip it. Recorded on ADR 0007 rather than left to be
  discovered by an operator pressing a key that does nothing.
- **In Textual, hiding a binding and disabling it are the same return value.**
  Sizing the footer through `check_action` disabled every action key at 80 columns.
  The narrow chrome is its own widget now.

## Notes for the next session

The working tree is clean and `main` is ahead of `origin/main` and unpushed - now
by 24 commits. Pushing has never been asked for. `git fetch` before surveying
anyway.

**The published design sheet is gone.** The artifact this file cites, and that
tickets 02 and 03 cite, no longer resolves for this account. Anything needing
those renders has to re-render them.

**One intermittent TUI test.** `test_edit_project_prepopulates_and_confirms_folder_rename`
failed once with a Textual `NoMatches` during a full run and has passed alone and
in four consecutive full runs since. Timing, not the session's work.

Prototype renderers for the wordmark and the three visual worlds live only in the
session scratchpad and are deliberately throwaway. They are not Atlas code. When
the wordmark ships, its glyph table, extrusion compositor and ramp sampler get
written fresh into `tools/atlas` under test - do not lift the prototype.

The published design sheet at
https://claude.ai/code/artifact/4a9756ec-d166-44d0-b76d-ddd9979fbbc6 is now out of
date in **two** ways, not one. It still draws missing folders inline in the tree,
which ticket 14 ruled out. And its renders are all 132x38, a width that ticket 03
established is not one the user actually works at. It has not been re-rendered and
the user has not said whether to.
