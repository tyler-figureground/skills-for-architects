# Do folders show a count, and of what

Type: grilling
Status: open
Blocked by: -
Parent: ../map.md

## Question

Raised by ticket 06, and cheap to settle - it may delete a whole class of cost from
the tree design before that design starts.

The prototypes show a file count beside each folder. Ticket 06 establishes that a
recursive count has no cheap primitive on either Win32 or the Drive API: a count *is*
a walk, exactly as expensive as loading that subtree. An immediate-child count is
free - it is `len()` of the `scandir` result the tree already holds to draw the node.

So the question is what the count is actually for.

- What does a studio user read a count to learn? The likely answer is "does this
  folder have work in it, or is it an empty shell" - which an immediate-child count
  answers completely.
- If that is the real question, recursive counts are removed from the design and the
  cost disappears. Confirm or reject.
- If recursive counts are genuinely wanted, they must be explicit, capped,
  cancellable, cached, and displayed as "n+" past the cap. Who triggers one, and
  what does it look like while it runs?
- Does an empty folder need a distinct treatment from a folder with contents? Atlas
  already has a clean command that removes file-empty folders, so emptiness is
  already a meaningful state in this product.
- Does a count distinguish files from subfolders, or is one number enough?
