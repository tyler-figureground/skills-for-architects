---
title: "Research: Reading a project tree over Google Drive File Stream"
date: 2026-09-02
generated_by: skills-for-architects
---

# Research: Reading a project tree over Google Drive File Stream

Research snapshot: September 2026.

- [HIGH | Primary-local] Scope context: Atlas reads Google Shared Drives mounted by Google Drive
  for desktop on Windows, default mount `G:\Shared drives`. Today's read is one `os.scandir` at the
  drive root plus one per project root, dirent-only, with recursive `os.walk` counts confined to
  relocation sources (`tools/atlas/src/atlas/core/scan.py`, `doctor.py`). The proposed navigable
  per-project tree with file counts is a materially larger read.
- [HIGH | Primary-local] Research handling: no repository code or private project data was sent to
  external services.
- [HIGH | Primary-local] **No production or shared drive was read, walked, or statted for this
  report.** Every question that can only be answered by a number from the real mount is listed in
  the validation queue with the measurement that would answer it. None of those measurements were
  run.

## Executive finding

- [HIGH | Primary] **The streaming case is the only case.** Google documents that "Shared Drives can
  only be streamed"; mirroring is available for My Drive and local folders only. Atlas never gets to
  design for a local copy of a shared drive, and there is no user setting that would give it one.
  [Stream and mirror files with Drive for desktop](https://support.google.com/drive/answer/13401938)
- [HIGH | Primary] **Enumeration is the unit of cost, not `stat`.** On Windows the directory
  enumeration itself carries attributes, sizes and timestamps, so `os.DirEntry.is_dir()`,
  `is_file()` and even `stat()` cost no additional system call except on symlinks. The correct
  budget model for a tree is *one enumeration per directory node you display*, and the correct
  discipline is to never touch an entry again after `scandir` returned it.
  [CPython `os` docs](https://github.com/python/cpython/blob/main/Doc/library/os.rst) ·
  [PEP 471](https://peps.python.org/pep-0471/)
- [HIGH | Primary] **Windows documents that enumerating a virtualized directory is more expensive
  than normal and may fetch from a remote store, and gives no number.** Google publishes no latency
  figure for Drive for desktop at all. Any millisecond budget in the Atlas UI must come from a
  measurement on a synthetic drive, not from a document.
  [File attribute constants](https://learn.microsoft.com/en-us/windows/win32/fileio/file-attribute-constants)
- [HIGH | Primary] **A per-folder recursive file count has no cheap primitive.** Neither Win32 nor
  the Drive API exposes a subtree count. A count *is* a walk. The only honest designs are: count
  immediate children (free, already in the `scandir` result you have), or make recursive counts
  lazy, cancellable, cached, and capped with an "n+" display.
  [`files.list` reference](https://developers.google.com/workspace/drive/api/reference/rest/v3/files/list)
- [HIGH | Primary] **Do not build the tree on Textual's `DirectoryTree` as it stands.** Its loader
  uses `Path.iterdir()` and then calls `Path.is_dir()` once in the sort key and once again in
  `_populate_node` - two `os.stat` calls per entry on top of the enumeration, and it never uses
  `os.scandir`. That is precisely the per-entry stat storm `scan.py` already warns about. Feed a
  plain `Tree` from `os.scandir` instead, or subclass and override the loader.
  [`_directory_tree.py`](https://github.com/Textualize/textual/blob/main/src/textual/widgets/_directory_tree.py)
- [HIGH | Primary] **Filesystem change notification is not a dependable staleness signal here.**
  `ReadDirectoryChangesW` "fails with **ERROR_INVALID_FUNCTION**" when the network redirector or
  target file system does not support it, caps its buffer at 64 KB over the network, and on overflow
  tells you to "compute the changes by enumerating the directory or subtree" - which is the walk you
  were trying to avoid. watchdog's own README already tells CIFS users to force `PollingObserver`.
  [ReadDirectoryChangesW](https://learn.microsoft.com/en-us/windows/win32/api/winbase/nf-winbase-readdirectorychangesw) ·
  [watchdog README](https://github.com/gorakhargosh/watchdog/blob/master/README.rst)
- [HIGH | Primary] **`Path.rglob` is the wrong instrument twice over.** pathlib documents that
  globbing with `**` "visits every directory in the tree. Large directory trees may take a long time
  to search", and that "Any `OSError` exceptions raised from scanning the filesystem are suppressed."
  On a flaky network-backed mount that second property is the dangerous one: a partial tree is
  returned as if complete, with no error, and Atlas would report absence where there is only
  failure. Atlas's whole value proposition is telling the studio what is missing.
  [pathlib docs](https://github.com/python/cpython/blob/main/Doc/library/pathlib.rst)

## Implementation-prioritized shortlist

| Priority | Change | Why now | Suggested Atlas shape | Evidence |
|---|---|---|---|---|
| P0 | Own the tree loader; do not use stock `DirectoryTree` | Stock widget spends two `os.stat` calls per entry on top of enumeration | `Tree[TreeNodeData]` fed by an `atlas.core` function that returns `(name, is_dir)` tuples from a single `os.scandir`, mirroring `scan.list_entries` | [HIGH \| Primary] [DirectoryTree source](https://github.com/Textualize/textual/blob/main/src/textual/widgets/_directory_tree.py) · [PEP 471](https://peps.python.org/pep-0471/) |
| P0 | Lazy expansion: one enumeration per expanded node, never a subtree | Enumeration of a virtualized directory is documented as more expensive than normal; depth is unbounded (shared drives allow 100 nesting levels) | Load children only on `NodeExpanded`; keep collapsed nodes unloaded; never pre-walk to compute a badge | [HIGH \| Primary] [RECALL_ON_DATA_ACCESS](https://learn.microsoft.com/en-us/windows/win32/fileio/file-attribute-constants) · [Shared drive limits](https://support.google.com/a/users/answer/7338880) |
| P0 | Every enumeration in a cancellable thread worker with a generation token | A single node expansion can block for an unbounded time on a network-backed mount | `@work(thread=True)` per node; tag each result with drive + generation; discard late results; per-node `loading` state and a real error state, not a silent empty folder | [HIGH \| Primary] [Textual workers](https://textual.textualize.io/guide/workers/) · [Textual issue #2056](https://github.com/Textualize/textual/issues/2056) |
| P0 | Surface enumeration errors as tree state, never as an empty node | `glob`/`rglob` suppress `OSError`; an empty node and an unreadable node must not look the same in a tool whose job is finding what is missing | Node states: unloaded / loading / loaded / error(reason) / truncated. `OSError` from `scandir` becomes `error`, with the exception text reachable | [HIGH \| Primary] [pathlib glob error suppression](https://github.com/python/cpython/blob/main/Doc/library/pathlib.rst) |
| P0 | Immediate-child counts only, free from the enumeration you already ran | Recursive counts have no cheap primitive anywhere in the stack | Show `n items` (dirs + files at this level) from `len()` of the `scandir` result. No recursive badge by default | [HIGH \| Primary] [`files.list`](https://developers.google.com/workspace/drive/api/reference/rest/v3/files/list) · [PEP 471](https://peps.python.org/pep-0471/) |
| P1 | Recursive count as an explicit, capped, cancellable action | A recursive count is a full subtree walk; it is a user-initiated operation, not a display property | `os.walk(followlinks=False)` in a worker with a node budget (e.g. stop at 5,000 files or 500 dirs) and a `5,000+` display; cache the result with the node's generation | [HIGH \| Primary] [`Lib/os.py` walk](https://github.com/python/cpython/blob/main/Lib/os.py) · [PEP 471](https://peps.python.org/pep-0471/) |
| P1 | TTL + explicit refresh instead of filesystem watching | Change notification is documented to fail outright on unsupported redirectors and to demand re-enumeration on overflow | Per-node `loaded_at`; consider a node stale after a TTL; `r` refreshes the focused node, `R` the whole tree. Follow rclone's shape: cache TTL 5m, poll 1m, poll interval strictly smaller than cache TTL | [HIGH \| Primary] [ReadDirectoryChangesW](https://learn.microsoft.com/en-us/windows/win32/api/winbase/nf-winbase-readdirectorychangesw) · [rclone mount](https://rclone.org/commands/rclone_mount/) |
| P1 | Cache enumerations in memory per session, keyed by path + generation | Repeated navigation over the same folders is the common interaction; re-enumerating on every collapse/expand multiplies the network cost with no new information | Dict keyed by `Path`, holding entries, `loaded_at`, and error state. Invalidate the subtree on any Atlas mutation of that subtree | [MEDIUM \| Primary-derived] [rclone `--dir-cache-time`](https://rclone.org/commands/rclone_mount/) · [PEP 471 throwaway `DirEntry` guidance](https://peps.python.org/pep-0471/) |
| P1 | No preview, no preload, no thumbnails, no content reads in the tree | Reading content is what actually hydrates a streamed file and consumes the local content cache | Tree shows names, kind, and immediate counts. Opening a file is an explicit action that hands off to the OS | [HIGH \| Primary] [Yazi network-file guidance](https://yazi-rs.github.io/docs/tips/) · [Cloud files hydration](https://learn.microsoft.com/en-us/windows/win32/cfapi/build-a-cloud-file-sync-engine) |
| P2 | Record placeholder/offline attributes if and only if they prove free | If the mount does expose `FILE_ATTRIBUTE_OFFLINE` / `RECALL_ON_*`, `entry.stat().st_file_attributes` gives Atlas an "on disk vs cloud-only" column for nothing | Read `st_file_attributes` from the `DirEntry` you already have; do not add a `Path.stat()` to get it. Gate on the validation-queue measurement | [MEDIUM \| Primary] [CF_PLACEHOLDER_STATE](https://learn.microsoft.com/en-us/windows/win32/api/cfapi/ne-cfapi-cf_placeholder_state) · [CfGetPlaceholderStateFromFindData](https://learn.microsoft.com/en-us/windows/win32/api/cfapi/nf-cfapi-cfgetplaceholderstatefromfinddata) |
| P2 | Drive API as a second read path, only if OAuth ever becomes acceptable | One paged listing can materialise an entire shared drive's node set in `ceil(N/1000)` requests, and `changes.list` gives authoritative staleness detection with one small call | `files.list` with `corpora=drive`, `driveId`, `supportsAllDrives`, `fields=nextPageToken,files(id,name,mimeType,parents)`, `pageSize=1000`; build the tree client-side. `changes.getStartPageToken` at load, `changes.list` to detect staleness | [HIGH \| Primary] [`files.list`](https://developers.google.com/workspace/drive/api/reference/rest/v3/files/list) · [Manage changes](https://developers.google.com/workspace/drive/api/guides/manage-changes) · [rclone `--fast-list`](https://rclone.org/drive/) |

## Findings

### How Drive for desktop presents a shared drive on Windows

- [HIGH | Primary] Streaming and mirroring are the two sync modes, and **"Shared Drives can only be
  streamed."** Mirroring applies to My Drive and to backed-up local folders. With streaming, "files
  are primarily stored in the cloud, but will be made available offline when accessed."
  [Stream and mirror files](https://support.google.com/drive/answer/13401938)
- [HIGH | Primary] The Windows presentation is a virtual drive: "The default streaming location is
  G:, but may be another location that you've configured." The `DefaultMountPoint` policy can set
  "a mounted drive letter or a path on an existing drive."
  [Set up Drive for desktop](https://knowledge.workspace.google.com/admin/drive/set-up-drive-for-desktop-for-your-organization) ·
  [Advanced configuration](https://knowledge.workspace.google.com/admin/drive/advanced-drive-for-desktop-configuration)
- [HIGH | Primary] Streaming maintains a local content cache. Default location on Windows is
  `%LOCALAPPDATA%\Google\DriveFS`; `ContentCachePath` relocates it; `ContentCacheMaxKbytes` bounds
  it and is "capped at 20% of the available space on the hard drive (regardless of the setting
  value)". `BandwidthRxKBPS` / `BandwidthTxKBPS` throttle transfer in kilobytes per second. Google
  documents this cache as holding **content**, and says nothing about whether directory metadata is
  cached locally or how long for.
  [Advanced configuration](https://knowledge.workspace.google.com/admin/drive/advanced-drive-for-desktop-configuration)
- [HIGH | Primary] Google's deployment guidance treats the virtual drive as something other
  software should be kept away from: virus detection and DLP tools "can interfere with the operation
  of Drive for desktop", and excluding the Drive for desktop directories from scanning is a
  documented troubleshooting step.
  [Set up Drive for desktop](https://knowledge.workspace.google.com/admin/drive/set-up-drive-for-desktop-for-your-organization)
- [HIGH | Primary] Shared drive shape limits that bound the worst case Atlas must survive: 500,000
  items per shared drive including files, folders, shortcuts and trash; up to 100 levels of nested
  folders; a warning banner once a drive passes 80% of the item limit. Google's own advice is to
  keep shared drives "well below the strict limit".
  [Shared drive limits](https://support.google.com/a/users/answer/7338880)
- [MEDIUM | Primary-derived] **Google does not document which Windows mechanism implements the
  virtual drive.** It documents that macOS 12.1 and later "uses File Provider" (Apple's on-demand
  file API) and offers no equivalent statement for Windows. Do not assume the Windows Cloud Files
  API. See *Contradictions and hidden variables* below.
  [Advanced configuration](https://knowledge.workspace.google.com/admin/drive/advanced-drive-for-desktop-configuration)

### What placeholder semantics say, where they apply

- [HIGH | Primary] Windows' cloud files API creates placeholder files that "consume only 1 KB of
  storage for the filesystem header, and that automatically hydrate into full files under normal use
  conditions." Files exist in three states: placeholder, full, and pinned full. The API is
  implemented by the `cldflt.sys` minifilter, which "currently only supports NTFS volumes because it
  depends on some features unique to NTFS."
  [Build a cloud file sync engine](https://learn.microsoft.com/en-us/windows/win32/cfapi/build-a-cloud-file-sync-engine)
- [HIGH | Primary] `FILE_ATTRIBUTE_RECALL_ON_OPEN` "only appears in directory enumeration classes
  (FILE_DIRECTORY_INFORMATION, FILE_BOTH_DIR_INFORMATION, etc.). When this attribute is set, it
  means that the file or directory has no physical representation on the local system; the item is
  virtual. Opening the item will be more expensive than normal, e.g. it will cause at least some of
  it to be fetched from a remote store."
  [File attribute constants](https://learn.microsoft.com/en-us/windows/win32/fileio/file-attribute-constants)
- [HIGH | Primary] `FILE_ATTRIBUTE_RECALL_ON_DATA_ACCESS`: "For a directory it means that some of
  the directory contents are being virtualized from another location. Reading the file /
  **enumerating the directory will be more expensive than normal**, e.g. it will cause at least some
  of the file/directory content to be fetched from a remote store." This is the closest thing to an
  official statement of enumeration cost anywhere in the stack, and it is qualitative.
  [File attribute constants](https://learn.microsoft.com/en-us/windows/win32/fileio/file-attribute-constants)
- [HIGH | Primary] Microsoft distinguishes **attribute-only opens** from data access and instructs
  minifilters not to convert one into the other: "A minifilter shouldn't issue reads/writes on
  intercepting attribute-only opens... such read/writes defeat the purpose of a minifilter checking
  for FILE_ATTRIBUTE_RECALL_ON_DATA_ACCESS." A metadata read is therefore not, by design, a content
  hydration - but `RECALL_ON_OPEN` still says opening a virtual item is more expensive than normal.
  The practical reading: a `stat` storm costs round trips, not downloads.
  [Handling placeholders](https://learn.microsoft.com/en-us/windows-hardware/drivers/ifs/placeholders_guidance)
- [HIGH | Primary] Placeholder state is derivable from data a directory enumeration already returns:
  `CfGetPlaceholderStateFromFindData` takes a `WIN32_FIND_DATA` "obtained from the
  FindFirstFile/FindNextFile functions" and returns `CF_PLACEHOLDER_STATE` -
  `PLACEHOLDER`, `IN_SYNC`, `PARTIAL`, `PARTIALLY_ON_DISK` ("its content is not fully present
  locally"), `SYNC_ROOT`, `NO_STATES`. So *where the cloud files API is in play*, "is this file
  actually on disk" is free at enumeration time.
  [CfGetPlaceholderStateFromFindData](https://learn.microsoft.com/en-us/windows/win32/api/cfapi/nf-cfapi-cfgetplaceholderstatefromfinddata) ·
  [CF_PLACEHOLDER_STATE](https://learn.microsoft.com/en-us/windows/win32/api/cfapi/ne-cfapi-cf_placeholder_state)
- [HIGH | Primary] The catch, and it is a large one: "the cloud files API always **hides its reparse
  points from all applications** except for sync engines and processes whose main image resides
  under `%systemroot%`." A normal Python process therefore does not see the reparse tag unless it
  calls `RtlSetProcessPlaceholderCompatibilityMode`. The attribute bits are a separate matter from
  the reparse point, but this is enough that Atlas must verify empirically what it can see, not
  assume.
  [Build a cloud file sync engine](https://learn.microsoft.com/en-us/windows/win32/cfapi/build-a-cloud-file-sync-engine)

### `os.scandir` and `DirEntry`: exactly what is free

- [HIGH | Primary] The CPython `os` documentation states it plainly: "All `os.DirEntry` methods may
  perform a system call, but `is_dir()` and `is_file()` usually only require a system call for
  symbolic links; `os.DirEntry.stat()` **always requires a system call on Unix but only requires one
  for symbolic links on Windows.**"
  [`Doc/library/os.rst`](https://github.com/python/cpython/blob/main/Doc/library/os.rst)
- [HIGH | Primary] PEP 471 gives the mechanism: "the Windows system calls return all the information
  for a `stat_result` object on the directory entry, such as file size and last modification time."
  `is_dir`, `is_file` and `is_symlink` are free on Windows because `FindNextFile` already returned
  the type. `scandir` reduces system calls "from approximately 2N to N", making `os.walk` "about
  8-9 times as fast on Windows".
  [PEP 471](https://peps.python.org/pep-0471/)
- [HIGH | Primary] The values are cached and never refreshed: "the `is_X` and `stat` methods cache
  their values (immediately on Windows via `FindNextFile`...) and never refetch from the system."
  PEP 471 is explicit that "DirEntry objects are intended to be used and thrown away after
  iteration, not stored in long-lived data structures."
  [PEP 471](https://peps.python.org/pep-0471/)
- [HIGH | Primary] The dirent data is not a guaranteed-fresh snapshot either. `FindNextFileW`:
  "In rare cases or on a heavily loaded system, file attribute information on NTFS file systems may
  not be current at the time this function is called." Enumeration order is also explicitly not
  guaranteed - "If the data must be sorted, the application must do the ordering after obtaining all
  the results."
  [FindNextFileW](https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-findnextfilew)
- [HIGH | Primary] `os.walk` is enumeration-bound, not stat-bound. `Lib/os.py` uses
  `with scandir(top) as entries`, decides recursion from `entry.is_dir()` (and `entry.is_symlink()`
  when not following links), and never calls `entry.stat()` in `walk()` - only `_fwalk()` does. On
  Windows all of those are satisfied from the dirent. A recursive count via `os.walk` therefore
  costs one enumeration per directory and nothing else.
  [`Lib/os.py`](https://github.com/python/cpython/blob/main/Lib/os.py)
- [MEDIUM | Primary] The correct implication for Atlas is a small correction to the `scan.py`
  docstring's phrasing. On Windows a `stat` is not free-because-cheap and not
  expensive-because-hydrating: it is expensive because `Path.stat()` on a path you already
  enumerated is a *second, separate* metadata operation against the mount, and `RECALL_ON_OPEN`
  documents an open on a virtual item as more expensive than normal. The behavioural rule the
  docstring encodes - stay dirent-driven, never re-stat - is right, and the evidence supports it more
  strongly than the "hydrates on stat" phrasing does.
  [File attribute constants](https://learn.microsoft.com/en-us/windows/win32/fileio/file-attribute-constants) ·
  [`Doc/library/os.rst`](https://github.com/python/cpython/blob/main/Doc/library/os.rst)
- [MEDIUM | Primary] CPython has actively optimised the Windows `os.stat` path: PR #102149, merged
  2023-03-16, adds use of `GetFileInformationByName()` "a newer Windows API that provides better
  performance than previous approaches", alongside the `st_ctime` deprecation and `st_birthtime`
  work. Whether that fast path is taken on a non-NTFS virtual volume is not documented; treat
  `Path.stat()` cost on the Drive mount as unmeasured.
  [PR #102149](https://github.com/python/cpython/pull/102149) ·
  [PR #99755 (superseded)](https://github.com/python/cpython/pull/99755)

### Documented latency for enumeration on a network-backed virtual filesystem

- [HIGH | Primary] **There is no official figure. Not from Google, not from Microsoft.** Microsoft's
  strongest documented statement is qualitative: enumerating a virtualized directory "will be more
  expensive than normal" and "will cause at least some of the file/directory content to be fetched
  from a remote store."
  [File attribute constants](https://learn.microsoft.com/en-us/windows/win32/fileio/file-attribute-constants)
- [HIGH | Primary] Google publishes throughput knobs (`BandwidthRxKBPS`, `BandwidthTxKBPS`) and cache
  bounds, and no latency characteristics of any kind for the virtual drive.
  [Advanced configuration](https://knowledge.workspace.google.com/admin/drive/advanced-drive-for-desktop-configuration)
- [HIGH | Primary] The only published numbers in the neighbourhood are rclone's, and they measure
  the **Drive API**, not the mounted filesystem: `--fast-list` batch requests "were up to 20x faster
  than the regular method", with worked examples of a small folder going 38s to 10s and a large
  folder going 22+ minutes to 58s. Useful as an order-of-magnitude argument for "one paged listing
  beats many per-folder round trips". Not transferable to `G:\` enumeration.
  [rclone Google Drive](https://rclone.org/drive/)
- [HIGH | Primary] Google's API-side rate model is documented and is the real ceiling on any
  API-based path: a `files.list` call costs 100 quota units, against 1,000,000 units per minute per
  project and 325,000 per minute per user per project, with truncated exponential backoff prescribed
  on 403/429.
  [Drive API usage limits](https://developers.google.com/workspace/drive/api/guides/limits)
- [HIGH | Primary-local] Consequence: **the Atlas tree cannot be given a latency budget from
  documentation.** The map's own standing constraint ("local timings are not a latency claim") is
  correct and remains unresolved by this research. See the validation queue.

### Per-folder file counts

- [HIGH | Primary] Immediate-child count is free. It is `len()` of the tuple `scandir` already
  returned, and `is_dir` on each entry costs nothing extra on Windows, so `n folders, m files` at a
  node carries zero marginal I/O once the node is loaded.
  [PEP 471](https://peps.python.org/pep-0471/)
- [HIGH | Primary] Recursive count has no cheaper primitive on the filesystem side. Win32 exposes no
  subtree count; `os.walk` is the primitive, and it costs one enumeration per directory in the
  subtree - which is the same work as expanding every node. The honest statement is that a recursive
  count for a node is exactly as expensive as loading that node's entire subtree.
  [`Lib/os.py`](https://github.com/python/cpython/blob/main/Lib/os.py)
- [HIGH | Primary] The Drive API has no count endpoint either. `files.list` pages at
  `pageSize` "maximum value is 1000; values above 1000 will be coerced to 1000", so counting a
  folder's children costs `ceil(n/1000)` list calls. What the API *does* offer that the filesystem
  cannot: a single paged listing scoped with `corpora=drive` + `driveId` returns every node in the
  shared drive with its `parents`, letting a client build the whole tree in `ceil(N/1000)` round
  trips instead of one round trip per folder. That is the technique rclone calls `--fast-list`.
  [`files.list`](https://developers.google.com/workspace/drive/api/reference/rest/v3/files/list) ·
  [rclone `--fast-list`](https://rclone.org/drive/)
- [HIGH | Primary] The `--fast-list` shortcut carries a documented shared-drive consistency hazard:
  "Files that were uploaded recently may not appear on the directory list sent to rclone when using
  `--fast-list`", with the advice to wait roughly an hour or not use it. A whole-drive listing is
  fast and is *less fresh* than a per-folder read.
  [rclone Google Drive](https://rclone.org/drive/)
- [HIGH | Primary-local] Atlas already has the right instinct in `doctor.py`: counts recurse "only
  into relocation-source folders, which are small by construction". Extending counts to arbitrary
  tree nodes removes that guarantee. Any recursive count in the tree needs an explicit budget and a
  truncated display.

### Detecting that a displayed tree has gone stale

- [HIGH | Primary] `ReadDirectoryChangesW` is the Windows notification primitive, and its
  documented failure modes are exactly the ones a virtual drive is likely to hit. "If the network
  redirector or the target file system does not support this operation, the function fails with
  **ERROR_INVALID_FUNCTION**." It "fails with **ERROR_INVALID_PARAMETER** when the buffer length is
  greater than 64 KB and the application is monitoring a directory over the network." And on
  overflow it "fails with **ERROR_NOTIFY_ENUM_DIR** when the system was unable to record all the
  changes to the directory. In this case, you should compute the changes by enumerating the
  directory or subtree."
  [ReadDirectoryChangesW](https://learn.microsoft.com/en-us/windows/win32/api/winbase/nf-winbase-readdirectorychangesw)
- [HIGH | Primary] watchdog wraps that API on Windows
  (`read_directory_changes.WindowsApiObserver`) and offers `polling.PollingObserver` as "fallback
  implementation". Its README documents the network case directly: "When you want to watch changes
  in CIFS, you need to explicitly tell watchdog to use `PollingObserver`." Polling means
  re-enumerating, which is the thing being avoided.
  [watchdog README](https://github.com/gorakhargosh/watchdog/blob/master/README.rst) ·
  [watchdog API](https://python-watchdog.readthedocs.io/en/stable/api.html)
- [HIGH | Primary] watchdog's snapshot layer carries a further caveat that matters on a synthetic
  filesystem: "This implementation does not take partition boundaries into consideration. It will
  only work when the directory tree is entirely on the same file system", and "any part of the code
  that depends on inode numbers can break if partition boundaries are crossed". Python's
  `os.stat` on Windows reports `st_ino`/`st_dev` unreliably to begin with.
  [watchdog API](https://python-watchdog.readthedocs.io/en/stable/api.html)
- [HIGH | Primary] The authoritative staleness signal for a shared drive is server-side, not
  filesystem-side. Drive API: call `changes.getStartPageToken()` for a token representing current
  state, then `changes.list(pageToken)` to retrieve changes since it, storing `newStartPageToken`
  for the next poll. `changes.watch()` adds push: "Notifications don't contain details about the
  changes. Instead, they indicate that new changes are available." One small call answers "has
  anything changed" for a whole drive.
  [Manage changes](https://developers.google.com/workspace/drive/api/guides/manage-changes)
- [HIGH | Primary] The documented pragmatic pattern, from a tool that mounts Drive for a living:
  rclone's VFS uses a time-based directory cache, `--dir-cache-time` default `5m0s`, described as
  controlling "how long a directory should be considered up to date and not refreshed from the
  backend", plus `--poll-interval` default `1m0s`, "Must be smaller than dir-cache-time. Only on
  supported remotes. Set to 0 to disable." Changes made through the VFS invalidate the cache
  immediately; external changes surface at the TTL or the poll.
  [rclone mount](https://rclone.org/commands/rclone_mount/)
- [MEDIUM | Primary-derived] A directory's own last-write time is the cheapest possible staleness
  probe (one metadata read per displayed node rather than a full enumeration), but nothing in the
  Windows documentation guarantees a virtual filesystem updates it on child add/remove, and
  `FindNextFileW` warns attribute data may not be current. Treat it as an optimisation to validate,
  never as the correctness mechanism.
  [FindNextFileW](https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-findnextfilew)
- [HIGH | Primary-local] The design that survives all of the above without new dependencies:
  Atlas invalidates the subtree it just mutated (it knows, because every mutation crosses a plan),
  ages everything else by TTL, and gives the operator a visible refresh. That is honest about the
  fact that a shared drive changes under you and no local signal will reliably tell you.

### Caching strategies for high-latency mounts that are actually documented

- [HIGH | Primary] **TTL'd directory cache with an optional change poll** - rclone: `--dir-cache-time`
  5m default, `--poll-interval` 1m default, poll strictly smaller than TTL, local writes invalidate
  immediately.
  [rclone mount](https://rclone.org/commands/rclone_mount/)
- [HIGH | Primary] **Batch the listing, not the folder** - rclone `--fast-list` "allows you to use
  fewer transactions in exchange for more memory... by combining multiple API requests using parent
  folder filters", up to 20x faster, at a documented freshness cost on shared drives.
  [rclone Google Drive](https://rclone.org/drive/)
- [HIGH | Primary] **Disable everything that touches content** - Yazi's first-party guidance: "For
  users managing network files, it's recommended to disable all previewers and preloaders since
  previewing and preloading these files means they need to be downloaded locally", with per-path
  rules (`url = "/remote/**"`, `run = "noop"`) so only the remote tree is affected.
  [Yazi tips](https://yazi-rs.github.io/docs/tips/)
- [HIGH | Primary] **Different index strategy per filesystem class** - Everything indexes fixed NTFS
  volumes automatically and maintains them "in real-time", but uses *folder indexing* for "mapped
  network drives, CDRoms, DVDRoms, FAT and FAT32 volumes" and file lists for offline media. A mature
  Windows indexer does not pretend one mechanism covers every mount.
  [Everything indexes](https://www.voidtools.com/support/everything/indexes/)
- [HIGH | Primary] **Lazy population in a worker** - Textual's own `DirectoryTree` loads on node
  expansion via `@work(thread=True, exit_on_error=False)` and a load queue; the maintainers' revisit
  issue lists "Populate the tree using a worker so that the application stays more responsive" as
  the responsiveness fix. The lazy-expansion shape is right even though the per-entry `is_dir` is
  not.
  [DirectoryTree source](https://github.com/Textualize/textual/blob/main/src/textual/widgets/_directory_tree.py) ·
  [Textual issue #2056](https://github.com/Textualize/textual/issues/2056)

### Negative evidence: approaches that look right and are documented to fail here

- [HIGH | Primary] **`Path.rglob` / `glob("**/...")`.** "Globbing with the `**` wildcard visits every
  directory in the tree. Large directory trees may take a long time to search." Worse for Atlas:
  "Any `OSError` exceptions raised from scanning the filesystem are suppressed. This includes
  `PermissionError` when accessing directories without read permission." A transient mount failure
  produces a short list, not an error - and Atlas would report a section as missing when it was only
  unreadable. `rglob` is "like calling `Path.glob()` with `**/` added in front of the pattern", so it
  inherits both properties.
  [pathlib docs](https://github.com/python/cpython/blob/main/Doc/library/pathlib.rst)
- [HIGH | Primary] **Stock `DirectoryTree`.** `_directory_content` iterates `location.iterdir()`;
  `_load_directory` sorts with `key=lambda path: (not self._safe_is_dir(path), path.name.lower())`;
  `_populate_node` then calls `allow_expand=self._safe_is_dir(path)`. `_safe_is_dir` is
  `path.is_dir()`. That is two `os.stat` calls per entry, on top of the enumeration, and
  `os.scandir` appears nowhere in the module. On a local disk this is invisible; on a streamed
  shared drive it is the dominant cost.
  [DirectoryTree source](https://github.com/Textualize/textual/blob/main/src/textual/widgets/_directory_tree.py)
- [HIGH | Primary] **Filesystem watching as the freshness mechanism.** Covered above:
  `ERROR_INVALID_FUNCTION` on unsupported redirectors, 64 KB buffer ceiling over the network,
  `ERROR_NOTIFY_ENUM_DIR` sending you back to a full enumeration, and watchdog's own instruction to
  fall back to polling on network filesystems.
  [ReadDirectoryChangesW](https://learn.microsoft.com/en-us/windows/win32/api/winbase/nf-winbase-readdirectorychangesw) ·
  [watchdog README](https://github.com/gorakhargosh/watchdog/blob/master/README.rst)
- [HIGH | Primary] **Assuming enumeration of a cloud-synced folder is even correct.** CPython issue
  #102993, open: `os.listdir` on a OneDrive/SharePoint sync folder of 897 files raises
  `OSError: [WinError 87] The parameter is incorrect`; deleting two files makes it succeed;
  `win32file.FindFilesIterator` yields 443 of 897 before failing; Explorer, `dir`, `ls` and `gci` all
  work, and a direct `NtQueryDirectoryFile` via ctypes returns the full list. Whatever the root
  cause, it is first-party evidence that Python's enumeration path over a synced folder has failure
  modes that native tools do not show. Atlas must handle a partial or failing enumeration as a state,
  not as a result.
  [CPython issue #102993](https://github.com/python/cpython/issues/102993)
- [HIGH | Primary] **Holding `DirEntry` objects to avoid re-reading.** PEP 471: the values are cached
  and "never refetch from the system"; objects "are intended to be used and thrown away after
  iteration, not stored in long-lived data structures." Atlas's existing pattern - convert to a
  frozen `Entry(name, is_dir)` inside the `with os.scandir(...)` block - is exactly right and should
  be the pattern for the tree too.
  [PEP 471](https://peps.python.org/pep-0471/)
- [MEDIUM | Primary] **Polling observers on a network mount as a safe fallback.** watchdog's own
  tracker carries "Polling Observer crashes on network loss" (#452) and related reports of observer
  threads dying when a mapped drive disconnects. A polling watcher on `G:\` adds a failure surface
  and buys re-enumeration Atlas could schedule itself.
  [watchdog #452](https://github.com/gorakhargosh/watchdog/issues/452)

## Contradictions and hidden variables

- **Cloud Files API placeholder semantics vs. Google's virtual drive** - split by *which Windows
  mechanism the vendor actually uses*. Nearly all placeholder documentation (`RECALL_ON_OPEN`,
  `CF_PLACEHOLDER_STATE`, hydration policies, 1 KB placeholders) describes the cloud files API, whose
  minifilter "currently only supports NTFS volumes". Google's default Windows presentation is a drive
  letter, i.e. its own volume, and Google documents adopting Apple's File Provider on macOS 12.1+
  while saying nothing equivalent for Windows. Microsoft-hosted Q&A additionally states CfAPI does
  not work for root partitions / drive letters, though that is a moderator answer, not reference
  documentation. **Resolution: unresolved, and deliberately left unresolved.** Treat the cfapi
  material as the best available model of *what a virtualized directory costs*, not as a description
  of Drive for desktop's implementation. Any Atlas feature that depends on reading placeholder state
  must be gated behind a measurement.
  [cfapi NTFS constraint](https://learn.microsoft.com/en-us/windows/win32/cfapi/build-a-cloud-file-sync-engine) ·
  [Advanced configuration](https://knowledge.workspace.google.com/admin/drive/advanced-drive-for-desktop-configuration) ·
  [Cloud File API FAQ (Microsoft Q&A, moderator answer)](https://learn.microsoft.com/en-us/answers/questions/2288103/cloud-file-api-faq)
- **"scandir is 8-9x faster on Windows" vs. "enumeration is the expensive part"** - split by
  *what dominates*. PEP 471's speedup is measured against local NTFS, where the win comes from
  halving system calls. On a network-backed mount the per-call latency dominates and the ratio is
  larger, not smaller - the advice points the same way for a different reason. But the *absolute*
  numbers in PEP 471 say nothing about `G:\`.
  [PEP 471](https://peps.python.org/pep-0471/)
- **Freshness vs. speed on the API path** - split by *listing granularity*. A whole-drive
  `files.list` is dramatically cheaper in round trips and documented to lag on shared drives
  (recently uploaded files may be absent for up to an hour). Per-folder reads are fresher and
  slower. There is no configuration that gets both.
  [rclone Google Drive](https://rclone.org/drive/)
- **`stat` hydrates vs. `stat` is an attribute-only open** - split by *what "expensive" means*.
  Microsoft's driver guidance explicitly protects attribute-only opens from being converted into
  data access, so a metadata read is not designed to download content; but `RECALL_ON_OPEN` still
  documents opening a virtual item as more expensive than normal. Both can be true: the cost of a
  stat storm is round trips, not bytes. Atlas's mitigation is unchanged either way.
  [Handling placeholders](https://learn.microsoft.com/en-us/windows-hardware/drivers/ifs/placeholders_guidance) ·
  [File attribute constants](https://learn.microsoft.com/en-us/windows/win32/fileio/file-attribute-constants)

## Survivorship-bias sweep

- [HIGH | Primary] **Watching over polling, abandoned for network filesystems.** watchdog ships a
  native Windows observer and still instructs users to switch to `PollingObserver` for CIFS; its
  tracker carries crash reports for polling observers on network loss and non-firing events on NFS.
  Nobody has made native notification work generally on remote mounts.
  [watchdog README](https://github.com/gorakhargosh/watchdog/blob/master/README.rst) ·
  [#452](https://github.com/gorakhargosh/watchdog/issues/452) ·
  [#504](https://github.com/gorakhargosh/watchdog/issues/504)
- [HIGH | Primary] **Real-time index, abandoned for non-NTFS.** Everything keeps its real-time NTFS
  index but falls back to folder indexing for mapped network drives and FAT volumes. The most
  optimised Windows file index in existence does not attempt real-time monitoring off NTFS.
  [Everything indexes](https://www.voidtools.com/support/everything/indexes/)
- [HIGH | Primary] **Per-folder API listing, abandoned for batch listing.** rclone's `--fast-list`
  exists because per-folder listing was too slow against Drive, and it is documented with the
  freshness regression that trade-off caused.
  [rclone Google Drive](https://rclone.org/drive/)
- [HIGH | Primary] **Eager tree population, abandoned in Textual itself.** The "Revisit
  DirectoryTree" issue lists worker-based population as the responsiveness fix, and the current
  implementation loads only on expansion. The remaining defect is the per-entry `is_dir`, which
  nobody has revisited.
  [Textual issue #2056](https://github.com/Textualize/textual/issues/2056)
- [MEDIUM | Primary] **`os.listdir` over synced folders, no abandonment - just an open bug.** CPython
  #102993 has no fix, no PR and no maintainer conclusion. The absence of a resolution is the
  finding: treat enumeration over a synced/virtual mount as fallible.
  [CPython #102993](https://github.com/python/cpython/issues/102993)
- **No abandonment evidence found** for: using `os.scandir` as the enumeration primitive (universally
  recommended, no counter-evidence); TTL-based directory caching (rclone's default for years);
  lazy expansion in TUI file trees.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Directory enumeration | `os.listdir` + `Path.stat()` per entry | `os.scandir`, converting to a frozen dataclass inside the `with` block | On Windows the enumeration already carries type, size and timestamps; a follow-up `stat` is a second round trip. `DirEntry` is documented as throwaway. [HIGH \| Primary] [PEP 471](https://peps.python.org/pep-0471/) |
| Recursive file count | Hand-rolled recursion with `Path.iterdir()` + `is_dir()` | `os.walk(path, followlinks=False)` | `walk` is scandir-based and calls no `entry.stat()`; it is already the cheapest correct subtree traversal in the stdlib. [HIGH \| Primary] [`Lib/os.py`](https://github.com/python/cpython/blob/main/Lib/os.py) |
| Finding files by pattern in a subtree | `Path.rglob("**/*.rvt")` | An explicit `os.walk` with your own error handling | `rglob` visits every directory *and* swallows every `OSError`, so failures read as absence. [HIGH \| Primary] [pathlib docs](https://github.com/python/cpython/blob/main/Doc/library/pathlib.rst) |
| Tree widget | Stock `DirectoryTree` | `Tree[T]` fed by an `atlas.core` enumeration function | Stock widget adds two `Path.is_dir()` calls per entry and never uses `scandir`. [HIGH \| Primary] [DirectoryTree source](https://github.com/Textualize/textual/blob/main/src/textual/widgets/_directory_tree.py) |
| Background loading + cancellation | Raw threads and polling flags | Textual `@work(thread=True)` with a generation token on results | Framework owns lifecycle and cooperative cancellation; thread workers cannot be force-cancelled, so the generation check is yours. [HIGH \| Primary] [Textual workers](https://textual.textualize.io/guide/workers/) |
| Detecting external changes | watchdog / `ReadDirectoryChangesW` on `G:\` | TTL + explicit refresh; Drive API `changes.list` if OAuth is ever in scope | Native notification is documented to fail outright on unsupported redirectors and to demand re-enumeration on overflow; watchdog itself prescribes polling for network filesystems. [HIGH \| Primary] [ReadDirectoryChangesW](https://learn.microsoft.com/en-us/windows/win32/api/winbase/nf-winbase-readdirectorychangesw) · [Manage changes](https://developers.google.com/workspace/drive/api/guides/manage-changes) |
| Cache invalidation policy | A bespoke heuristic | rclone's shape: per-directory TTL, optional poll strictly shorter than the TTL, immediate invalidation on your own writes | Documented, defaulted, and battle-tested against Drive specifically. [HIGH \| Primary] [rclone mount](https://rclone.org/commands/rclone_mount/) |
| Whole-drive listing (if the API path is taken) | Per-folder `files.list` walk | One paged `files.list` with `corpora=drive` + `driveId` + `parents` in the field mask | `ceil(N/1000)` requests instead of one per folder; documented up to 20x faster in rclone's measurements, with a documented freshness caveat. [HIGH \| Primary] [`files.list`](https://developers.google.com/workspace/drive/api/reference/rest/v3/files/list) · [rclone](https://rclone.org/drive/) |
| Placeholder / offline state | Custom cfapi P/Invoke and reparse-tag parsing | `entry.stat().st_file_attributes` from the `DirEntry` you already hold - *if* the bits prove visible | cfapi hides its reparse points from ordinary processes; the attribute bits, if present, arrive free with the enumeration. Gate on measurement. [MEDIUM \| Primary] [cfapi reparse-point hiding](https://learn.microsoft.com/en-us/windows/win32/cfapi/build-a-cloud-file-sync-engine) |

## Validation queue

Everything in this section needs a number or a behaviour from the real mount. **None of it was
measured. Per the ticket's constraint, no production or shared drive was touched.** The measurements
below should be run against a synthetic Google Workspace account with a purpose-built shared drive,
or - if that is not available - explicitly authorised as a one-off read against the studio drive.

- [LOW | Requires measurement] **Cost of one `os.scandir` on a cold, never-visited project folder on
  `G:\`.** The single most load-bearing unknown in the tree design. Measure at 10, 100 and 1,000
  entries, cold (Drive for desktop restarted, content cache cleared) and warm. Without this there is
  no lazy-load budget and no defensible spinner threshold.
- [LOW | Requires measurement] **Marginal cost of `Path.stat()` per entry on the same folder**, to
  quantify the stock-`DirectoryTree` penalty and to confirm or correct the `scan.py` docstring's
  cost model.
- [LOW | Requires measurement] **Whether `entry.stat().st_file_attributes` on the Drive mount carries
  `FILE_ATTRIBUTE_OFFLINE`, `RECALL_ON_OPEN` or `RECALL_ON_DATA_ACCESS`, and whether
  `st_reparse_tag` is populated.** Determines whether an "on disk vs cloud-only" column is free,
  cheap, or impossible.
- [LOW | Requires measurement] **What `GetDriveType` reports for `G:\`, and whether
  `ReadDirectoryChangesW` on it returns `ERROR_INVALID_FUNCTION`.** One tiny probe decides whether
  filesystem watching is even on the table or must be written off in the tree-states design.
- [LOW | Requires measurement] **Whether a Drive folder's directory mtime changes when a child is
  added or removed.** If yes, a one-metadata-read staleness probe per visible node is viable; if no,
  TTL plus explicit refresh is the only mechanism.
- [LOW | Requires measurement] **Whether Drive for desktop caches directory metadata locally and for
  how long** - i.e. does a second enumeration of the same folder cost materially less, and does that
  survive an app restart. Google documents only a *content* cache. This determines whether an Atlas
  in-memory cache is a real win or a duplicate of one the mount already keeps.
- [LOW | Requires measurement] **Enumeration behaviour on a folder with several thousand entries**,
  given CPython #102993. Confirm `os.scandir` returns a complete list and does not fail or truncate.
- [LOW | Implementation-time validation] Confirm the recursive-count budget (proposed: stop at 5,000
  files or 500 directories) against the studio's actual largest project, using the count Atlas itself
  reports rather than a separate walk.
- [LOW | Product validation] Confirm the studio actually wants recursive counts. If immediate-child
  counts answer the real question ("is this folder empty / does it have work in it"), the entire
  recursive-count cost disappears from the design.
- [LOW | Scope validation] Whether an OAuth-authenticated Drive API path is acceptable at all for
  Atlas. It is the only route to authoritative staleness detection and to sub-linear whole-drive
  listing, and it is a large change in what Atlas is: credentials, token storage, offline failure
  modes, and a second source of truth alongside the drive map.

## Source quality summary

- [HIGH | Primary] Microsoft Windows documentation: file attribute constants (`RECALL_ON_OPEN`,
  `RECALL_ON_DATA_ACCESS`, `OFFLINE`), the cloud files API portal and sync-engine guide,
  `CF_PLACEHOLDER_STATE`, `CfGetPlaceholderStateFromFindData`, `FindNextFileW`,
  `ReadDirectoryChangesW`, and the IFS "Handling placeholders" driver guidance.
- [HIGH | Primary] Python: PEP 471, CPython `Doc/library/os.rst` and `Doc/library/pathlib.rst`,
  `Lib/os.py`, and the CPython issue tracker (#102993, PR #102149, PR #99755).
- [HIGH | Primary] Google first-party: Drive Help (stream vs mirror, Drive for desktop),
  Workspace admin knowledge base (advanced Drive for desktop configuration, org setup), shared drive
  limits, and the Drive API developer guides (`files.list`, manage changes, usage limits).
- [HIGH | Primary] First-party tool documentation and source: Textual `DirectoryTree` source and
  issue #2056, watchdog README/API docs and tracker, rclone mount and Drive backend docs, Yazi tips,
  Everything (voidtools) index documentation.
- [MEDIUM | Microsoft-hosted Q&A] The Cloud File API FAQ answers are moderator-written, not reference
  documentation. Used only as corroboration for the CfAPI/drive-letter question, which is left
  unresolved.
- [MEDIUM | Synthesis] The Atlas-specific shortlist and the cost model infer fit from primary
  evidence plus the local code's constraints. No latency figure in this report comes from a
  measurement, because none was permitted or run.
