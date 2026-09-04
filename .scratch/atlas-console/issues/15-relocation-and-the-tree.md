# What the tree does when conform moves things

Type: grilling
Status: resolved
Blocked by: -
Parent: ../map.md

## Question

Raised by ticket 05. `TreeNode` has no re-parent API - Textual discussion 6133 is
open on exactly this - so a node cannot be moved from one parent to another once
built. Conform's whole job is moving folders: drift renames, relocations, sweeps.

So after an applied plan, the tree has to do one of three things, and the map has
not said which:

1. **Refresh the affected subtree.** Rebuild from the nearest common ancestor.
   Correct, and costs a re-enumeration of everything under it - expensive on a
   streaming mount per ticket 06.
2. **Patch node by node.** Remove the source node, insert at the target. Cheap, and
   it means the tree's model and disk can diverge if the plan half-applied. Atlas
   already reports partial results with Done / Skipped / Conflict / Failed per item.
3. **Invalidate and make the user re-expand.** Honest, cheapest, worst to use.

Resolve:

- Which, and does it differ between a single-node action and a batch conform?
- Ticket 05 also proves the cursor is restored by *line number*, not node identity,
  so a rebuild with a different child list silently moves the selection somewhere
  else. What is Atlas's selection-restore key, and where does re-resolution happen?
- What does the tree show for a node whose plan came back Conflict or Failed? That
  state is real, durable, and currently has no representation.
- Does an external change - someone else moving a folder on the shared drive -
  reach the tree at all, or only through explicit refresh? Ticket 06 rules out
  filesystem watching.

## Resolution

Folded into `docs/adr/0007` and built with the seam - the questions could not be
answered before the structure existed. Ticket 21's Move Manifest turned out to
answer most of them.

- **Which of the three.** Neither option 1 as written nor option 2. **Invalidate by
  manifest.** The manifest names exactly which folders changed, so `reconcile`
  forgets the parent of each source and each destination - the same two directories
  the scoped Guard watched. Two enumerations, not a walk from a common ancestor.
  A project-wide conform invalidates the project instead, because its manifest can
  span everything. Invalidation strength scales with action scope, the way guard
  strength does.
- **Selection restore key.** The **Node Key** - the project-relative path.
  `follow(key, applied)` maps a pre-write key to its post-write one from the
  manifest, so the cursor follows the thing it just repaired instead of landing on
  whatever now occupies that line. A merge needed the Action as well as the
  manifest: it moves children one at a time and nothing in the manifest names the
  folder that vanished.
- **Conflict or Failed.** No new state. A conflicted merge leaves the source in
  place with its colliding children in it, and the tree draws that truthfully
  because it is a mirror. The outcome is reported on the operation line and in the
  Companion, where ADR 0005 already put write outcomes. Filing State says what the
  map says, not what happened.
- **External change.** Only through the 60-second shelf life or an explicit
  refresh. Ticket 06 ruled out watching and nothing here reopens it.
