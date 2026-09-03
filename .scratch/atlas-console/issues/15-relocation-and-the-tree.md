# What the tree does when conform moves things

Type: grilling
Status: open
Blocked by: 04
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
