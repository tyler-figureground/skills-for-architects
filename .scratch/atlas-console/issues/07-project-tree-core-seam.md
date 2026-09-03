# The ProjectTree core seam

Type: grilling
Status: open
Blocked by: 04, 05, 06
Parent: ../map.md

## Question

The TUI owns interaction; `atlas.core` owns filesystem facts. The tree needs a seam
between them that does not leak Textual into core or filesystem walking into the
TUI, and `tui/model.py` is the precedent - a pure presentation model the tests cross.

Resolve, once the write contract and both research tickets are in:

- What structure does core hand the TUI for one project? A node tree, a flat list
  with depth, or a lazily-expanding handle?
- How do map facts attach to nodes: expected-but-absent, drift source and target,
  relocation, sweep, unfiled, empty. `doctor.report_project` already computes most
  of these against the project as a whole - does the tree reuse that report or need
  its own pass?
- Where does the not-on-disk list come from, and is it derived from the same
  structure as the tree or computed separately? The chosen tree model is a
  filesystem mirror with the missing set beside it, not merged into it.
- Eager or lazy: does core walk the whole project once, or hand back expandable
  nodes the TUI pulls on demand? Ticket 06 constrains this.
- File counts: computed at walk time, on demand, or not at all.
- Is the structure immutable and regenerated, like `ProjectRow`, or mutated in place
  as nodes expand?
- What does the CLI do with this seam, if anything - is there an `atlas tree`
  command, and does it share the structure?

Record the vocabulary in `/CONTEXT.md` and the seam in `.agent/handoff/`. This is
the ticket most likely to earn an ADR.
