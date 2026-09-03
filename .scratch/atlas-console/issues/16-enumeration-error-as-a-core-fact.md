# Enumeration failure as a core fact

Type: grilling
Status: resolved
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

## Evidence from ticket 12

No longer hypothetical. A read-only walk of the live studio drive found two
directories that raise `FileNotFoundError` from `os.scandir` while their own
parents list them without trouble. Both are `MAX_PATH` - 259 and 273 characters -
and both read correctly through the `\\?\` extended-length prefix.

```
path length 273
  atlas list_entries()     -> 0 entries  (indistinguishable from empty)
  reality via \\?\ prefix  -> 1 entries
  MISREPORT: True
```

So the false negative this ticket was opened about is happening today, on
production data, in a folder that has contents.

Two things this pins down that the ticket previously left open:

- **`find_empty_dirs` is not at risk.** `os.walk` uses `onerror=None`, so a
  failing directory is omitted from the walk entirely; it is never yielded as a
  root, never enters `empties`, and because it still appears in its parent's
  `dirs` list the `all(...)` test at `ops.py:264` fails and the parent is not
  marked empty either. Verified. The failure mode is false reporting, not
  destruction - so this ticket is about correctness, not safety.
- **The trigger is path length, not permissions.** Whatever `list_entries`
  returns instead must be able to say *which* failure, because `MAX_PATH` has a
  fix (ticket 19) and a permission error does not.

Report: `docs/research/atlas-drive-latency-measurement.md`

## Answer

Built and shipped. `uv run pytest` 211 passed (was 201), `./scripts/lint.sh`
passed, and both live failing paths verified fixed against the real drive.

**`list_entries` returns a `Listing`, not a tuple.** It carries a Load State
(`read` / `unreadable`, with `partial` modelled but not yet produced), the entries,
and the error string. `readable` is the property callers check.

Two design choices worth recording:

- `Listing` implements `__iter__` and `__len__`, so all six existing consumers -
  five in `doctor`, one in the TUI's project token - needed no change at all.
- It also defines `__bool__` returning `True` unconditionally. Without that,
  `__len__` would make `if listing:` false for an unreadable directory, which is
  precisely the bug this type exists to prevent. There is a test pinning it.

**Every caller's behaviour:** unchanged, because they all iterate. The one place
that had to change is `report_project`, which now records the failure and refuses
to call the project `conform`.

**Status when a project root is unreadable: `unfiled` (REVIEW).** Not `stub` -
that means "no canonical sections found", which claims Atlas looked and saw
nothing. Not a fifth status: ADR 0004 deliberately left the project statuses
alone, and REVIEW already means "a person has to look at this". If REVIEW proves
too coarse once the tree lands, a distinct status is a small follow-up.

**`--json` gains an `unreadable` key** per project. The existing
`test_report_json_shape` pins the exact key set and failed on the change, which is
what it is for; it was updated deliberately and now also asserts the key is empty
on a healthy project. Exit codes are unchanged: an unreadable project reports
`unfiled`, which was already exit 1.

**The TUI detail pane** gets a `COULD NOT READ` block, above `REVIEW REQUIRED` and
never folded into it, plus the headline "Cannot read - Atlas could not open part of
this project" and the line "Nothing above is trustworthy for this project."

**Partial enumeration is modelled but not detected.** `PARTIAL` exists in the Load
State constants and nothing produces it. The drive-cost research found no reliable
way to notice a short enumeration - CPython issue 102993 returns fewer entries with
no error at all. Recorded rather than faked.

### Residual scope, stated plainly

`report_project` checks the **project root only**, because that is all `scan_drive`
enumerates today. A folder three levels down that cannot be read is still invisible
to `doctor`. The two live failures are exactly that shape - they are deep inside
projects, and after the fix they read fine, so nothing is currently hidden. But the
general case waits for the tree, which enumerates deeply and where `Listing` is
already the return type. Ticket 07 inherits this.

### Verified on the live drive

```
path length 259 -> state read, readable True, 0 entries   (genuinely empty)
path length 273 -> state read, readable True, 1 entries: ['02 Sheets']
```

Before the fix the second returned zero entries and claimed to be empty. Whole-drive
scan and report: 14 projects, 404 ms, zero unreadable.
