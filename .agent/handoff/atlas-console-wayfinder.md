---
title: "Atlas console redesign - wayfinder continuity"
date: 2026-09-02
generated_by: skills-for-architects
---

# Atlas console redesign - wayfinder continuity

Status: world locked, both research tickets in, awaiting wordmark decision
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

## Frontier

Unblocked and unclaimed: 03, 04, 08, 10, 11, 12, 13, 14, 16.
Claimed: 02, waiting on the user.
Blocked: 07 (on 04, 13, 14, 16), 09 (on 03), 15 (on 04).
Resolved: 01, 05, 06.

Two tickets want the user specifically rather than any session: **02** (which
wordmark treatment, where the header collapses, how far the retro register
travels) and **12** (provision a synthetic Workspace shared drive, or authorise a
one-off read of the studio drive, so the tree can be given a latency budget).

Good first ticket for a fresh session with no user present: **14**, the node kind
vocabulary. Nothing blocks it, it is pure `/domain-modeling`, and it unblocks both
the token layer and the tree seam.

## Warning for the next session

The working tree carries roughly thirty modified and untracked files from the intake,
contacts, and editing work, and `main` is ahead of `origin/main` by one. Ticket 01
exists to land it. Do not start implementation tickets on top of that tree - the
diffs will be unreadable. `git fetch` before surveying, as always.
