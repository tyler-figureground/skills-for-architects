# Extended-length paths

Type: grilling
Status: open
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
