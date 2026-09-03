# Do folders show a count, and of what

Type: grilling
Status: resolved
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

## Answer

**Immediate-child counts only. No recursive counts anywhere in the tree.**

Three arguments, the third decisive:

1. **It answers the real question.** What a person reads a count for is "is there
   work in this folder or is it an empty shell". The immediate count answers that
   completely.
2. **It is free.** The count is `len()` of the enumeration already held to draw the
   node. A recursive count is a walk: measured at 0.53 ms per folder warm and about
   3.2 ms cold, so a 500-folder subtree costs 0.3 to 1.6 seconds to produce one
   number.
3. **Lazy loading forbids it anyway.** A node whose Load State is Unread has no
   count without reading it, and a recursive count would need every descendant
   read. Showing recursive counts and loading lazily are mutually exclusive. Lazy
   loading is already settled.

**Counts render only on folders whose Load State is Read.** An Unread folder shows
no count - never a zero, which would be the same false-negative shape as the
unreadable-versus-empty bug. In practice most visible folders will have a count,
because ticket 12 already budgets a one-level-ahead prefetch: expanding a folder
reads its children, and the prefetch reads *their* children, which is exactly what
produces counts for the rows on screen.

**Format: folders and files counted separately.** "2 folders, 14 files", or a
compact "2F 14" in a narrow pane. One combined number would hide the distinction
that actually matters when deciding whether a folder holds deliverables or just
more structure.

### The collision this uncovered

`ops.find_empty_dirs` defines empty as **"no file anywhere beneath"** - recursive -
and `clean` deletes on that basis. `CONTEXT.md` had just defined **Empty Folder**
as a folder with no children of its own - immediate. Two different predicates
sharing one word, and one of them removes folders.

A folder holding a chain of subfolders that contain no files is Fileless and
deletable, but is *not* an Empty Folder. Left unnamed, the tree would badge one
thing "empty" while `clean` acted on another, and the first person to notice would
be someone whose folder disappeared.

Named in `/CONTEXT.md`:

- **Empty Folder** - Read, no children of its own. What the tree badges.
- **Fileless** - no file anywhere beneath. What Clean removes.

Every Empty Folder is Fileless; most Fileless folders are not Empty Folders. The
tree must never label a Fileless-but-not-Empty folder as empty, and must never
imply Clean will leave an Empty Folder alone.

Whether the tree surfaces Fileless at all - a "clean can remove this" hint on a
node - is left to ticket 04, which owns what the tree is allowed to do.
