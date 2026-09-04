# The ProjectTree core seam

Type: grilling
Status: resolved
Blocked by: -
Parent: ../map.md

## Question

The TUI owns interaction; `atlas.core` owns filesystem facts. The tree needs a seam
between them that does not leak Textual into core or filesystem walking into the
TUI, and `tui/model.py` is the precedent - a pure presentation model the tests cross.

Resolve, once the write contract and both research tickets are in:

- What structure does core hand the TUI for one project? A node tree, a flat list
  with depth, or a lazily-expanding handle?
- How do map facts attach to nodes? Ticket 14 names the kinds; this decides where
  they live on the structure, along with drift and relocation targets. `doctor.report_project` already computes most
  of these against the project as a whole - does the tree reuse that report or need
  its own pass?
- Where does the not-on-disk list come from, and is it derived from the same
  structure as the tree or computed separately? The chosen tree model is a
  filesystem mirror with the missing set beside it, not merged into it.
- Eager or lazy: ticket 06 answers this - lazy, one `os.scandir` per displayed
  node, never re-touching an entry. What remains is the shape of the handle the
  TUI pulls on, and where cancellation lives.
- File counts: ticket 13 settles whether recursive counts exist at all. Immediate
  child counts are free from the `scandir` result already in hand.
- Staleness: ticket 06 rules out filesystem watching over a redirector. TTL plus
  explicit refresh plus subtree invalidation on Atlas's own mutations is the
  documented shape - decide the TTL and where invalidation is triggered.
- Partial and failed enumeration are distinct states the structure must be able to
  carry. See the tree-states fog on the map.
- Is the structure immutable and regenerated, like `ProjectRow`, or mutated in place
  as nodes expand?
- What does the CLI do with this seam, if anything - is there an `atlas tree`
  command, and does it share the structure?

Record the vocabulary in `/CONTEXT.md` and the seam in `.agent/handoff/`. This is
the ticket most likely to earn an ADR.

## Constraints already fixed

From ticket 05, binding on whatever this seam produces:

- The TUI side is a plain `Tree`. `DirectoryTree` destroys injected nodes on
  reload, its only subclass hook can subtract paths but never add them, and it
  costs ~2 `is_dir()` stats per entry per load where `os.scandir` costs zero.
- Per-node styling has exactly one route: `render_label`. Tree nodes are not DOM
  nodes and take no CSS.
- Labels must be `rich.text.Text`, never `str`. `Tree.process_label` runs
  `Text.from_markup`, so a real folder named `[b] Basement Survey` silently loses
  its prefix - and `[2024]` survives, which is what makes it latent.
- Selection is restored by line number, not node identity. The seam must expose a
  stable key the TUI re-resolves against after every refresh.
- Per-node load workers must not be `exclusive` - that would cancel every other
  in-flight expansion sharing the widget's default worker group.

## Resolution

`atlas.core.tree`, built test-first alongside the decision. 15 tests; whole suite
294, up from 281. Recorded in `docs/adr/0007`, vocabulary in `/CONTEXT.md` under
Atlas Project Tree Seam.

Answers, in the order the ticket asked:

- **Structure.** A lazily-expanding handle, `ProjectTree`. Immutable `TreeNode`
  values out, mutable cache inside. Not a node tree (eager, which ticket 06 ruled
  out) and not a flat list with depth (bakes TUI expansion state into core).
- **Map facts.** The tree reuses `doctor.report_project` rather than running a
  second pass. Below the root, where the report has no opinion, **containment**
  decides: at or under a canonical path is Mapped, under an Unfiled node is
  Unfiled, and a path the map names explicitly keeps its own verdict at any depth.
- **Not-on-disk list.** Computed from the map and the root listing, separately from
  the tree, per the filesystem-mirror model. The ticket's framing was incomplete on
  one point: **only control-plane Expectations are repairable.** Conform has never
  created a mapped section and `_apply_backfill` would skip it, so an Expectation
  carries its kind and a missing section keeps the add-folders path.
- **Eager or lazy.** Lazy, one enumeration per displayed folder. Cancellation lives
  in the TUI worker; every core call is side-effect free, so an abandoned one costs
  the read and nothing more.
- **Counts.** Immediate children only, free from the enumeration already held.
- **Staleness.** 60-second shelf life, explicit refresh, invalidation by Move
  Manifest on Atlas's own writes. An external change is invisible until one of the
  first two - stated, not hidden.
- **Partial and failed enumeration.** Carried through from `Listing`, which already
  models both. A folder Atlas could not open never renders as empty.
- **Immutable or mutated.** Nodes immutable and regenerated; the handle mutable.
- **CLI.** No `atlas tree` here. The seam is pure core and could carry one; whether
  it should is ticket 10's call, along with search and the dossier.

Inherited and still open: `report_project` checks the project root only, so a
folder three levels down that cannot be read is invisible to `doctor`. Ticket 16
recorded it; this seam carries it forward rather than closing it.
