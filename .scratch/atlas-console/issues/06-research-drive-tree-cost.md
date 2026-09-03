# Reading a project tree over Google Drive File Stream

Type: research
Status: resolved
Blocked by: -
Parent: ../map.md

## Question

Atlas runs against Google Shared Drives mounted through Drive for Desktop. Its
current scan is shallow - project directories and section presence. A navigable
folder tree with file counts is a materially heavier read, and the prior smoke test
explicitly disclaimed its local timings as not a Drive latency claim.

Answer, with primary sources - Google Drive for Desktop documentation, Python
`os`/`pathlib` reference, CPython source or issues, and first-party issue trackers:

- How Drive for Desktop presents a mounted shared drive to the filesystem API on
  Windows: streaming versus mirrored mode, placeholder files, and what a `stat` or
  `scandir` on a not-yet-downloaded item actually costs.
- Whether `os.scandir` avoids extra `stat` calls there, and which `DirEntry`
  attributes are free versus which trigger a round trip.
- Published or documented latency characteristics for directory enumeration on a
  network-backed virtual filesystem, and whether any figures are official.
- Caching strategies other file managers use for high-latency mounts - what is
  actually documented, not folklore.
- Whether file counts per folder can be obtained more cheaply than a full walk, and
  what the honest cost of a per-node count is.
- How to detect that a displayed tree has gone stale without re-walking.
- Negative evidence: approaches that look right and are documented to fail here -
  recursive globbing, `Path.rglob` over a mount, watchdog-style filesystem
  notification on a virtual drive.

Capture as a confidence-tiered report under `docs/research/`. No branch; ticket 01
owns the working tree. Do not touch a production or shared drive to measure - if a
measurement is needed, say so and stop rather than reading the live drive.

Do not expose repository code externally.

## Answer

Report: `docs/research/atlas-drive-tree-read-cost.md` (uncommitted, on `main`; ticket 01 owns the
working tree). Confidence-tiered, primary sources only, direct URLs throughout. No production or
shared drive was read, walked, or statted; every question needing a number is in the validation
queue, unmeasured and marked as such.

Top conclusions:

1. **Shared drives are streaming-only.** Google documents that shared drives cannot be mirrored, so
   the network-backed virtual-drive case is the only case Atlas will ever face. There is no user
   setting that yields a local copy.

2. **Enumeration is the unit of cost, not `stat`.** On Windows the dirent already carries type,
   size and timestamps: `DirEntry.is_dir()`, `is_file()` and `stat()` cost no extra system call
   except on symlinks (CPython `os` docs, PEP 471). Budget one `scandir` per displayed node and
   never touch an entry again. `scan.py`'s dirent-only discipline is correct; its "hydrates on
   stat" phrasing is imprecise - the documented cost of a stat storm is extra round trips
   (`RECALL_ON_OPEN`: "opening the item will be more expensive than normal"), not content
   downloads, since Microsoft explicitly protects attribute-only opens from becoming data access.

3. **No official latency figure exists anywhere.** Microsoft says enumerating a virtualized
   directory "will be more expensive than normal" and gives no number; Google publishes none at
   all. The map's "local timings are not a latency claim" constraint stays unresolved - a tree
   latency budget requires a measurement on a synthetic drive, which this ticket forbade and which
   was therefore not run.

4. **Per-folder recursive counts have no cheap primitive.** Neither Win32 nor the Drive API has a
   subtree-count call; a count *is* a walk, exactly as expensive as loading that subtree. Immediate
   child counts are free (`len()` of the `scandir` result already in hand). Recursive counts must
   be explicit, capped, cancellable, cached, and displayed as `n+`.

5. **Do not use stock Textual `DirectoryTree`.** It uses `Path.iterdir()` then calls
   `Path.is_dir()` twice per entry (sort key plus `_populate_node`) and never uses `os.scandir` -
   two `os.stat` calls per entry on top of enumeration, the precise storm to avoid. Its
   lazy-expansion-in-a-worker shape is right; feed a plain `Tree` from `atlas.core` instead.

6. **Filesystem watching is not a dependable staleness signal.** `ReadDirectoryChangesW` returns
   `ERROR_INVALID_FUNCTION` on unsupported redirectors, caps at 64 KB over the network, and on
   overflow tells you to re-enumerate; watchdog's own README prescribes `PollingObserver` for
   network filesystems. Use TTL plus explicit refresh plus subtree invalidation on Atlas's own
   mutations - the rclone shape (dir cache 5m, poll 1m, poll < TTL). Authoritative detection exists
   only server-side via Drive API `changes.list`, which means OAuth.

7. **Negative evidence: `Path.rglob` fails twice.** Documented to visit every directory, and
   documented to suppress every `OSError` including `PermissionError` - so a transient mount failure
   returns a short tree with no error. For a tool whose product is "what is filed and what is
   missing", silent truncation is the worst possible failure. Also: CPython issue #102993 (open) has
   `os.listdir` raising `WinError 87` and `FindFilesIterator` returning 443 of 897 files on a
   OneDrive/SharePoint sync folder while Explorer and `dir` work fine. Enumeration over a synced
   mount is fallible; partial reads must be a tree state, not a result.

Unresolved contradiction worth carrying: Google does not document which Windows mechanism backs the
virtual drive. Nearly all placeholder documentation describes the Cloud Files API, whose minifilter
is NTFS-only, while Drive mounts a drive letter by default and Google documents File Provider only
for macOS. The cfapi material is the best available model of what a virtualized directory costs -
not a description of Drive's implementation. Any feature reading placeholder state must be gated on
a measurement.
