---
title: "Atlas console redesign - wayfinder continuity"
date: 2026-09-02
generated_by: skills-for-architects
---

# Atlas console redesign - wayfinder continuity

Status: first code shipped; header and token layer are next
Date: 2026-09-02
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

## Frontier

Unblocked and unclaimed: 03, 04, 08, 10, 11, 13, 17, 18.
Blocked: 07 (on 04, 13), 09 (on 03), 15 (on 04).
Resolved: 01, 02, 05, 06, 12, 14, 16, 19.

**17 and 18 are the build path.** 18 first - the token layer decides where the
ember palette and the node glyph table live, and 17 wants those colours. Both were
waiting on 14, which is done.

**07 is close.** It needs 04 and 13, both small decisions and both unblocked. 04 is
the tree write contract, 13 is whether folders show a count at all - and 13 may
delete a whole class of cost before the seam is designed.

## Notes for the next session

The working tree is clean and `main` is ahead of `origin/main` and unpushed. That
was ticket 01, and it is resolved - the warning that used to live here no longer
applies. `git fetch` before surveying anyway.

Prototype renderers for the wordmark and the three visual worlds live only in the
session scratchpad and are deliberately throwaway. They are not Atlas code. When
the wordmark ships, its glyph table, extrusion compositor and ramp sampler get
written fresh into `tools/atlas` under test - do not lift the prototype.
