# Node kind vocabulary

Type: grilling
Status: resolved
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

## Answer

Recorded in `/CONTEXT.md` under "Atlas Project Tree" and in
`docs/adr/0004-tree-node-filing-state-and-load-state.md`.

**The candidate list in the question was wrong in two ways, and both matter.**

**One: "mapped but missing" is not a node kind.** The locked tree model is a
filesystem mirror with unmet expectations listed separately. A folder the map
wants and disk lacks has no path to expand, no children, no sibling order that
means anything, and one possible action. Making it a node forces every consumer of
a node to special-case it. It is an **unmet Expectation**, and it lives in the list
beside the tree.

*This contradicts the prototypes.* The renders on the sheet draw missing folders
inline as dim hatched rows AND list them under NOT ON DISK - showing the same fact
twice, and violating the model that was chosen at charting. The tree renderer
drops the inline rows; the NOT ON DISK list stays. Flagged rather than quietly
changed, because it changes what the approved picture looks like.

**Two: kind is not one axis, it is two.** The candidate list mixed "what the map
says about this folder" with "what Atlas knows about its contents", which are
independent. A Mapped folder can be Unreadable. An Unfiled folder can be Unread.
Collapsing them into one enum produces states like "unfiled-but-also-unreadable"
that multiply.

**Filing State** - exactly one of Mapped, Drifted, Misplaced, Loose, Unfiled,
resolved by the first map rule that matches, in the order conform already applies
them: drift renames, relocations, sweeps, then Unfiled as the fallthrough.

**Load State** - folders only, one of Unread, Read, Unreadable, Partial.

Emptiness is derived, not stored. A folder is empty only when Read with no
children; Unread, Unreadable and Partial folders are never called empty. This is
what makes the ticket 12 finding renderable - the folder with one entry that
Atlas currently shows as empty becomes Unreadable instead.

### The table, without a legend

| Filing State | Reads as | Fill | Colour |
|---|---|---|---|
| Mapped | filed correctly | solid `█` | ready |
| Drifted / Misplaced / Loose | Atlas can fix this | hatched `▚` | action |
| Unfiled | you have to decide | hatched `▚` | review |

Solid versus hatched answers "is anything wrong". Colour answers "is it mine or
Atlas's". The specific state name appears in the label, so a first-timer never has
to decode a glyph they have not seen.

Load State renders as the disclosure indicator plus, where it is not Read, an
explicit label: `cannot read` for Unreadable, `partial` for Partial. Neither ever
renders as blank or as an empty folder.

### The confirmed palette change

Ticket 02 moved `SETUP` from steel blue to warm bronze without being asked, and
asked this ticket to confirm it. **Confirmed.** SETUP is a project status, not a
Filing State, so it does not appear in the tree at all - which removes the last
reason to keep a blue on screen. Nothing in the node table needs a colour outside
the ember family.

### Scope note

The existing project-level statuses `conform` / `drift` / `unfiled` / `stub` and
their TUI labels READY / ACTION / REVIEW / SETUP are unchanged. They answer a
different question. The overlap between `drift` the project status and `Drifted`
the Filing State is the main cost of this decision and is recorded in the ADR.
