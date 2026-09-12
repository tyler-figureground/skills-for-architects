# AGENTS.md holds the instructions, and CLAUDE.md points at it

Every mapped project carries two agent files at its root. `AGENTS.md` holds the instructions and the index — the house working style, and where the control plane lives. `CLAUDE.md` holds one line, `@AGENTS.md`, and nothing else.

Claude Code reads `CLAUDE.md`; Codex and most other coding agents read `AGENTS.md`. Writing the instructions twice guarantees they diverge, and the copy that drifts is the one nobody opened. A one-line import makes Claude Code read the same file every other agent reads, with no second copy to maintain.

The pointer is relative on purpose. A person had already written this convention by hand on the live drive, with an absolute path into the project folder; the folder was renamed a week later and the pointer went stale, pointing at a path that no longer existed. `@AGENTS.md` survives a rename because it never names the folder.

Atlas owns a marker-wrapped block inside `AGENTS.md` — `<!-- atlas:agents-begin -->` to `<!-- atlas:agents-end -->` — carrying the working style and an index built from the drive map, the same way `PROJECT.md` carries a regenerable canonical-map block. Everything outside the markers belongs to the project: its own posture, its code strategy, its model traps. Conform refreshes the block and never touches a line outside it.

## The two writes that are not creations

Control-plane backfill has been constructive only: create what is missing, report a conflict, never overwrite. Two bounded exceptions follow from this decision, and both are bounded by a check rather than by good intentions.

**The Atlas block is refreshed in place.** Only the lines between the markers are replaced. Broken markers — a begin without an end, or two of either — are a conflict, not a guess.

**A non-pointer `CLAUDE.md` is rewritten to the pointer**, but only after conform can prove the words are not lost: either the file is byte-for-byte what Atlas and the PS1 tools used to generate (stock, safe to discard because the same facts are regenerated in the new index), or every non-blank line of it already appears, in order, inside `AGENTS.md`. Anything else is a conflict left in place for a person to merge. In a full plan the `AGENTS.md` backfill runs first and seeds itself from the project's own `CLAUDE.md`, so the proof is normally satisfied by the migration that just happened.

Neither write is invertible by the undo stack — a backfill has no Move Manifest, and `invert_plan` already refuses a plan containing one. The content is recoverable because it is in `AGENTS.md`, not because Atlas can put it back.

## Consequences

`atlas doctor` reports `AGENTS.md` when it is absent or its Atlas block is missing or stale, and `CLAUDE.md` when it is absent or carries anything but the pointer. Both read the file, so doctor now opens two more small files per project.

Names are matched exact-case. A hand-saved `Agents.md` reads as missing on a case-insensitive mount, and conform renames it through a temp name rather than creating a second file it could never see.

`agentsFile` defaults to `AGENTS.md` with no map entry, so the convention reaches every mapped drive. A map may set it empty to opt out, in which case `CLAUDE.md` keeps the pre-0.4 full-text content and is only ever created.

Atlas 0.3 and earlier do not know the name: a project conformed by this version reports `AGENTS.md` as unfiled in an older Atlas until the drive's pinned wheel is updated.
