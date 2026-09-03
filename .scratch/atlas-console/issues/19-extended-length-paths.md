# Extended-length paths

Type: grilling
Status: resolved
Blocked by: -
Parent: ../map.md

## Question

Found while measuring for ticket 12. Two folders on the live studio drive cannot
be enumerated by their ordinary paths because they exceed `MAX_PATH` - 259 and 273
characters - and both read correctly through the `\\?\` extended-length prefix.

Windows applies the 260-character limit to normal paths but not to paths prefixed
`\\?\`. The prefix also disables all path normalisation: no `..` resolution, no
forward-slash translation, no relative paths, no short-name expansion.

The studio's own folder convention makes this recurring rather than freak. Project
folders are `YYMMDD_<street address>-<description>`, sections nest two or three
deep, and Revit backup folders repeat the full project name inside the project.
One of the two failures is exactly that: the project name appearing four times in
its own path.

Resolve:

- Does Atlas prefix every path it touches, prefix only when a path approaches the
  limit, or not at all and report the failure instead?
- If it prefixes, where? A single chokepoint in core that every filesystem call
  passes through, or at each call site? A chokepoint is the only maintainable
  answer, and Atlas does not currently have one.
- The prefix disables normalisation, so every path handed to it must already be
  absolute and normalised. What breaks if a relative path reaches it? What does
  the drive map's forward-slash notation become?
- Does it change what `PROJECT.md`, `_Project Index.md`, and `--json` record?
  Those are read by other tools and by people.
- Conform *moves* folders. A relocation can lengthen a path past the limit even
  when both endpoints looked fine. Does plan-building check the resulting length
  and refuse, or does it prefix and proceed?
- Should `atlas doctor` report over-long paths as a finding in their own right?
  The studio may want to know, independently of whether Atlas can cope.
- Windows can also enable long paths system-wide via registry or manifest. Is
  relying on that acceptable, given the drive is shared with other machines whose
  configuration Atlas does not control? The safe assumption is no.

Interacts with ticket 16, which owns what `list_entries` returns when enumeration
fails; this ticket owns whether it should have failed at all.

## Answer

**Prefix on demand, at a chokepoint, for reads.** `scan.long_path()` returns a
path string Windows will accept, applying `\\?\` only when the path is 240
characters or longer and only on Windows. It absolutises first, because the prefix
disables all normalisation, and handles the UNC form.

**Why on demand rather than always.** The prefix turns off `..` resolution,
forward-slash translation, relative paths and short-name expansion. Applying it to
every path would mean auditing every path Atlas constructs for absoluteness and
separator style, and silently changing behaviour for the 99.9% of paths that were
never near the limit. The threshold is 240 rather than 260 to leave headroom for a
child name appended to a directory path.

**Where it is applied:** the three read chokepoints - `scan.list_entries`,
`scan.count_files`, and `doctor._dir_exists_exact`'s per-segment walk. Those are
every enumeration in core.

**Where it is deliberately NOT applied yet: writes.** `conform` and `ops` build
paths for renames, moves and directory creation and were left alone. That is a
scope decision, not an oversight:

- A move can lengthen a path past the limit even when both endpoints looked fine,
  so the right fix is a length check in plan-building that refuses or warns, not a
  blind prefix that lets Atlas create paths other tools cannot open.
- Explorer, Revit and the PowerShell tools that share this drive do not all handle
  long paths. Atlas making a path only Atlas can read would be a worse outcome
  than refusing.

That check belongs to the conform work and is now named in the map's fog.

**System-wide long paths are not relied on.** The registry/manifest opt-in exists
but the drive is shared with machines Atlas does not configure, so the safe
assumption is that it is off.

**Not added: a doctor finding for over-long paths.** Considered and deferred. The
studio may well want to know, but it is a new finding type with its own severity,
JSON key and TUI treatment, and it is not needed for correctness now that the reads
work. Left in the fog.

Verified: a synthetic 300-character path is created and read in
`tests/test_scan.py`, skipped off Windows; and both real 259/273-character folders
on the studio drive now enumerate correctly.
