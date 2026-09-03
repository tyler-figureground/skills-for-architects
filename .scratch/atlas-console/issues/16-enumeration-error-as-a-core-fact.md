# Enumeration failure as a core fact

Type: grilling
Status: open
Blocked by: -
Parent: ../map.md

## Question

Raised by ticket 05, and verified in the source: `atlas.core.scan.list_entries`
catches `OSError` and returns an empty tuple (`tools/atlas/src/atlas/core/scan.py`
lines 58-59). The TUI therefore cannot tell "this folder is empty" from "this
folder could not be read".

For a tool whose entire product is *what is filed and what is missing*, those two
must never look alike. An unreadable folder rendered as empty is a false negative
that reads as fact.

This is a core seam change, not a TUI change, which is why it is its own ticket
rather than a line in the tree-states fog.

Resolve:

- What does `list_entries` return instead? A result type carrying entries or an
  error, an exception the caller handles, or a sentinel?
- Every existing caller - `scan`, `doctor`, `conform`, `ops` - currently reads an
  empty tuple as "no entries". What does each do when the answer becomes "unknown"?
  A project whose sections cannot be read must not be reported as conforming, and
  must not be reported as drifted either.
- Ticket 06 adds a second case: enumeration can return a *partial* result. CPython
  issue 102993 shows `os.listdir` returning 443 of 897 entries on a synced mount
  with no error at all. Is partial a third state, and can Atlas even detect it?
- Does conform refuse to build a plan over an unreadable subtree, or build a plan
  that excludes it and says so?
- What does `--json` emit, and does an unreadable folder change the exit code?
  Atlas uses 0 clean, 1 findings, 2 error.

`/tdd` applies - this is core, and every branch above wants a test.
