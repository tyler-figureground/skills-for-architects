# What the folder tree is allowed to write

Type: grilling
Status: open
Blocked by: -
Parent: ../map.md

## Question

File-level actions are in scope: creating a folder the map expects, renaming a
drifted folder, filing an unfiled item into its mapped home, revealing in Explorer.
Every one of those except reveal is a mutation on the live studio drive, triggered
from a tree node by a single keystroke.

Atlas today puts a core-built plan, an exact preview, and a confirmation in front of
every write, and never overwrites a destination.

Resolve:

- Does every tree action build a core plan and confirm, with no exceptions? The
  proposed answer is yes - the same contract conform already meets.
- If yes, what does confirmation look like for a single-node action, where a modal
  listing one line is heavier than the action itself? Is there a lighter confirm
  that is still honest?
- Is there any action cheap and reversible enough to skip confirmation - creating an
  empty mapped folder, for instance - and if so what makes it safe?
- Is there undo, or is preview-then-confirm the whole safety story? The prior
  critique scored user control 2/4 specifically for having no undo.
- What happens when the drive changed underneath a displayed tree? The existing code
  uses stale-plan fingerprints; does the tree carry the same guarantee?
- Do tree actions get CLI equivalents, or is this the first TUI-only capability?
  Interacts with the CLI-parity ticket.
