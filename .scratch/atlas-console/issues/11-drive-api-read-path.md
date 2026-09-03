# An authenticated Drive API read path

Type: grilling
Status: open
Blocked by: -
Parent: ../map.md

## Question

Raised by ticket 06, which the map had no slot for.

Everything Atlas does today reads the mounted filesystem. Ticket 06 establishes
that this is the only case Atlas faces - Google shared drives are streaming-only
and cannot be mirrored - and that the filesystem gives no authoritative way to
know a displayed tree has gone stale.

An OAuth-authenticated Google Drive API read path would change that. It is the only
documented route to authoritative staleness detection (`changes.list`) and to
sub-linear whole-drive listing: one paged `files.list` scoped to a `driveId` builds
the entire tree in `ceil(N/1000)` requests, rather than one enumeration per folder.

It also costs a great deal. Resolve:

- Is an authenticated API path acceptable for Atlas at all, or is filesystem-only a
  standing constraint of the tool?
- It introduces a second source of truth about folder structure. The map's standing
  constraint is that `_tools/<drive>-map.json` is the only folder-structure brain -
  does an API listing violate that, or is it a cache of the same disk truth?
- Credentials: where does a token live on a studio machine, who provisions it, what
  happens when it expires, and what does Atlas do offline or unauthenticated?
- Would it be read-only, always? Writes must keep crossing filesystem core plans.
- Is it worth it only for search and staleness, or does the tree read from it too?

A defensible answer is "no, filesystem only" - in which case record why, and the
tree accepts TTL-based staleness and a per-folder enumeration cost forever.
