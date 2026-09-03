---
title: "Atlas: measured enumeration cost on a live Google Shared Drive"
date: 2026-09-02
generated_by: skills-for-architects
---

# Atlas: measured enumeration cost on a live Google Shared Drive

Resolves ticket 12 of the `atlas-console` map. Companion to
`atlas-drive-tree-read-cost.md`, which established from primary sources what
*should* be true and closed with "no official latency figure exists anywhere."
This supplies the figures that research could not.

Date: 2026-09-02
Machine: Windows 11 Pro 26200, Google Drive for Desktop, `G:` mount
Authorisation: the user explicitly authorised reading the studio drive for this
measurement, with no mutation and nothing created.

## Safety of the method

Every measurement in this document was produced by `os.scandir` and
`DirEntry.is_dir()` and nothing else. No `open`, no `stat`, no `mkdir`, no
`rename`, no `unlink`, no write of any kind reached any drive. No file or folder
was created on any shared drive, so there was nothing to delete afterwards. The
benchmark scripts were audited for write calls before being run and lived only in
the session scratchpad.

`DirEntry.is_dir()` is free here: the companion research established that on
Windows the directory entry already carries the type, so it costs no additional
system call except on symlinks.

## What was measured

| Target | Character |
|---|---|
| `ARCHITECTURE` | The working studio drive. Used daily, so Drive's local metadata cache is warm. |
| `LIBRARY - Reference` | Reference material, rarely walked. The closest available proxy for cold. |

Three runs: a bounded breadth-first walk of each, and one uncapped walk of the
whole studio drive.

## The numbers

### Whole studio drive, uncapped

| | |
|---|---|
| folders enumerated | **7,956** |
| files seen | **18,536** |
| wall clock | **4.24 s** |
| mean per folder | **0.53 ms** |
| p50 / p90 / p99 | 0.40 / 0.67 / 1.78 ms |
| max | 27.72 ms |
| calls over 50 ms | **0** |
| enumeration errors | 2 (see below) |

Depth made almost no difference: p50 stayed between 0.38 ms and 0.61 ms from
depth 1 to depth 13.

### Warm versus cold

| | working drive (warm) | rarely-walked drive |
|---|---|---|
| scans | 3,000 | 2,500 |
| p50 | 0.49 ms | 0.77 ms |
| p90 | 0.98 ms | 1.74 ms |
| p99 | **2.47 ms** | **91.49 ms** |
| max | 29.26 ms | **314.49 ms** |
| over 50 ms | 0 | 37 |
| over 200 ms | 0 | 4 |
| over 1 s | 0 | 0 |

**This is the headline.** The median is essentially free on both. The difference
lives entirely in the tail: on material Drive has not cached, roughly 1.5% of
enumerations took more than 50 ms and the worst took 314 ms. Nothing anywhere took
a second.

### Concurrency

Eight worker threads against folders neither walk had touched:

| drive | serial (30 folders) | 8 workers (30 folders) | speedup |
|---|---|---|---|
| `ARCHITECTURE` | 11.31 ms | 5.27 ms | 2.15x |
| `LIBRARY - Reference` | 20.30 ms | 11.13 ms | 1.82x |

Sub-linear. A small pool captures most of the available gain; a large one would
mostly contend.

## The budgets ticket 12 asked for

Derived from the figures above. Each is a starting value with the reasoning
attached, not a law.

**Loading-state threshold: 120 ms.** Cold p99 is 91 ms and the observed worst case
is 314 ms, so a spinner shown immediately would flash and vanish on essentially
every expansion. 120 ms sits above the cold p99 and near the perceptual boundary
where a delay stops feeling instant. At p90 of 1.74 ms, the overwhelming majority
of expansions will never show it at all.

**Prefetch: one level ahead of the cursor, capped at 50 nodes, cancellable.**
Thirty sibling folders cost 11-20 ms typically. The same thirty could cost 9.4 s
if every one of them landed in the cold tail, which is why the cap and the
cancellation matter more than the number.

**Concurrency cap: 4 in-flight node loads.** Measured speedup is 1.8x-2.15x at
eight workers, so the curve has already flattened. Four captures most of it and
leaves the shared thread pool available for scans and mutations. Ticket 05
separately establishes these workers must not be `exclusive`.

**Recursive count cap: 500 folders, and show `n+` beyond it.** At 0.53 ms per
folder warm and about 3.2 ms cold, 500 folders is roughly 0.3 s to 1.6 s. Ticket 13
may delete this entirely by choosing immediate-child counts, which are free.

**Cache TTL: 60 s.** Enumeration is cheap enough that a short TTL costs almost
nothing, and short is what makes an external change on a shared drive visible in
reasonable time. Filesystem watching is ruled out by the companion research.

## The finding that outranks the timings

**A full walk of the entire studio drive takes 4.24 seconds.** That reframes
several open tickets:

- A drive-wide search index is affordable. Ticket 08 was written assuming a
  whole-drive walk might be prohibitive; at four seconds it is not.
- Lazy loading is still correct, but for responsiveness under a cold tail, not
  because the total is large.
- The performance anxiety in the map was not wrong to have, but it was aimed at
  the wrong risk. The risk is not throughput. It is the 300 ms outlier and the
  failure modes below.

## Two enumeration failures on live production data

The uncapped walk hit two directories that raised `FileNotFoundError` while being
listed by their own parents.

| path length | outcome |
|---|---|
| 259 chars | `os.scandir` fails; `\\?\` extended-length prefix succeeds; genuinely empty |
| 273 chars | `os.scandir` fails; `\\?\` extended-length prefix succeeds and returns **1 entry** |

Both are `MAX_PATH`. The parent lists the child, the child cannot be opened by its
normal path, and the extended-length prefix reads it correctly.

**Atlas currently mis-reports the second one.** `atlas.core.scan.list_entries`
catches `OSError` and returns an empty tuple, so Atlas sees zero entries for a
folder that contains one. Verified directly against the installed core:

```
path length 273
  atlas list_entries()     -> 0 entries  (indistinguishable from empty)
  reality via \\?\ prefix  -> 1 entries
  MISREPORT: True
```

This is ticket 16's hypothesis confirmed on production data, not a synthetic case.

### What is *not* at risk

`find_empty_dirs` uses `os.walk`, whose default `onerror` silently omits a failing
directory from the walk entirely. The failing directory is therefore never yielded
as a root and never added to `empties`; and because it still appears in its
parent's `dirs` list, the `all(...)` test at `ops.py:264` fails and the parent is
not marked empty either. Verified: `os.walk` from the parent does not yield the
failing directory.

So `atlas clean` will not delete these folders or their parents. The failure mode
is **false reporting, not destruction.** Worth stating plainly, because the
opposite conclusion would have been easy to jump to.

## Limitations, stated plainly

- **"Cold" is a proxy.** Drive for Desktop's metadata cache cannot be observed or
  cleared from user space. "Cold" here means material this machine has not walked
  recently, on a drive the user does not work in daily. A genuinely first-touch
  read on a freshly provisioned machine could be slower than 314 ms. These figures
  are a floor.
- **One machine, one network, one moment.** No claim is made about a different
  office, a VPN, or a Saturday.
- **This drive is small.** 7,956 folders. A drive an order of magnitude larger may
  exceed whatever Drive for Desktop is willing to keep cached, and the warm numbers
  would then look like the cold ones.
- **No writes were measured**, because none were permitted. Mutation cost on this
  mount is still unknown, and conform is a mutation-heavy operation.

## Recommended follow-ups

1. Ticket 16 gets this as its evidence. `list_entries` must distinguish failure
   from emptiness.
2. A new decision: whether Atlas uses the `\\?\` extended-length prefix for every
   path it touches. It demonstrably works on this drive and would fix both
   failures, but it changes every path Atlas constructs.
3. Re-run this benchmark once the tree ships, against the same drive, to catch a
   regression in enumeration discipline.
