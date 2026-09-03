# Node kind vocabulary

Type: grilling
Status: open
Blocked by: -
Parent: ../map.md

## Question

Raised by ticket 05. `/CONTEXT.md` has no term for what a tree node *is*, and two
separate pieces of work key off that term: `render_label`, which ticket 05 proves
is the only route to per-node styling because tree nodes are not DOM nodes and take
no CSS, and the token layer that owns the glyph and colour for each state.

Name the kinds. The candidate set, from what the drive actually contains:

- on disk and mapped - the folder exists and the drive map expects it
- on disk and unfiled - the folder exists and the map does not know it
- on disk and drifted - exists under a name the map renames to something else
- mapped but missing - the map expects it and disk does not have it
- unreadable - enumeration failed. Distinct from empty. See ticket 16.
- not yet loaded - lazy node whose children have not been fetched
- file - a leaf, not a folder

Resolve:

- Is that the right set, is it too fine, and does anything collapse?
- Does a node carry exactly one kind, or is kind orthogonal to load state? A folder
  can be both unfiled and not-yet-loaded.
- Where do drift target and relocation target live - on the node, or beside it?
- What is each kind's glyph and colour in the locked POCHE world, and what does a
  first-time user read without a legend? Ticket 02 chose fill weight; this is where
  that becomes a table.
- Does the CLI use the same vocabulary in `--json`?

Land the terms in `/CONTEXT.md` with `/domain-modeling`. This blocks the token
layer and it blocks the tree seam.
