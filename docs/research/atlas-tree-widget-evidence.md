---
title: "Research: Textual 8.2.8 tree widgets and lazy loading"
date: 2026-09-02
generated_by: skills-for-architects
---

# Research: Textual 8.2.8 tree widgets and lazy loading

Research snapshot: September 2026. Target version is the one `tools/atlas` locks:
`textual>=8.2,<9`, resolved 8.2.8 (released 2026-06-30).

- [HIGH | Primary-local] Scope context: build the Atlas project folder tree on Textual
  8.2.8, over Google Shared Drive project folders on Windows. The tree must show both
  what is filed on disk and what the drive map expects but disk lacks.
- [HIGH | Primary-local] Research handling: no repository code or private project data
  was sent to external services. All local evidence came from reading the installed
  package and running synthetic fixtures.
- [HIGH | Primary] The Textual 8.2.8 source installed in `tools/atlas/.venv` is
  byte-identical to the `v8.2.8` git tag for both `_tree.py` and `_directory_tree.py`
  (verified by `diff`). Every source citation below is a permalink pinned to that tag,
  so line numbers are exact for the version Atlas runs.

## How the measured claims were produced

- [HIGH | Primary-local] Behavioral and timing claims marked *measured* come from probe
  scripts run under the Atlas venv on Python 3.12.13 / Windows 11 (24 CPUs), driving real
  widgets through Textual's own `App.run_test()` harness at 132x38.
- [HIGH | Primary-local] Timings are **local NTFS on synthetic fixtures**. Per the Atlas
  map, local timings are not a latency claim about Google Drive File Stream. They are
  used here only to compare *relative* cost and to count syscalls, which is the quantity
  that Drive latency multiplies.

## Executive finding

- [HIGH | Primary] **Build the Atlas tree on plain `Tree`, not `DirectoryTree`.** Three
  independent reasons, each individually sufficient. (1) `DirectoryTree` cannot durably
  hold a node that is not on disk: `_populate_node` calls `node.remove_children()` before
  repopulating from `iterdir()`, so any injected node is destroyed on the next load or
  reload (measured: injected node gone after `reload_node`). (2) `DirectoryTree` costs
  about **2.0 `is_dir()` stat calls per directory entry per load** (measured: 202
  `is_dir()` / 203 `stat()` for one load of a 100-entry directory), where `atlas.core.scan`
  deliberately uses `os.scandir` and pays **zero** extra syscalls, because the Drive mount
  hydrates placeholders on stat. (3) Its only additive extension point is `filter_paths`,
  which can subtract paths but never add them.
  [`_populate_node`](https://github.com/Textualize/textual/blob/v8.2.8/src/textual/widgets/_directory_tree.py#L477-L491) ·
  [`filter_paths`](https://github.com/Textualize/textual/blob/v8.2.8/src/textual/widgets/_directory_tree.py#L441-L454) ·
  [`os.scandir`](https://docs.python.org/3/library/os.html#os.scandir)
- [HIGH | Primary] **Lazy expansion is a supported pattern, and `DirectoryTree` is the
  reference implementation to copy, not to inherit.** `TreeNode.expand()` posts
  `Tree.NodeExpanded` before children exist, so a handler can populate on demand.
  `DirectoryTree` does exactly this through a queue plus a thread worker per directory.
  Maintainer `davep` points people at it for precisely this reason.
  [`_add_to_load_queue`](https://github.com/Textualize/textual/blob/v8.2.8/src/textual/widgets/_directory_tree.py#L187-L204) ·
  [`_loader`](https://github.com/Textualize/textual/blob/v8.2.8/src/textual/widgets/_directory_tree.py#L529-L561) ·
  [discussion 2730](https://github.com/Textualize/textual/discussions/2730)
- [HIGH | Primary] **Scrolling is genuinely virtualized; rebuilding is not.** Rendering
  touches only visible lines (measured: 38 strips rendered whether the tree holds 500 or
  5000 lines; warm re-render 0.0-0.1ms). But `Tree._build()` walks every expanded node and
  calls `render_label` once per line, and any mutation, resize, or style change invalidates
  it. Measured full rebuild at 5000 expanded nodes: **20-30ms**. The scaling risk is
  rebuild frequency, not scroll.
  [`_build`](https://github.com/Textualize/textual/blob/v8.2.8/src/textual/widgets/_tree.py#L1252-L1298) ·
  [`_invalidate`](https://github.com/Textualize/textual/blob/v8.2.8/src/textual/widgets/_tree.py#L1074-L1079)
- [HIGH | Primary] **Overriding `get_label_width` is a documented, and now measured, 4x
  win.** The default implementation renders the whole label just to measure it. A cheap
  override cut the median full rebuild at 5000 nodes from **25.4ms to 6.4ms**. The source
  docstring explicitly invites this override.
  [`get_label_width`](https://github.com/Textualize/textual/blob/v8.2.8/src/textual/widgets/_tree.py#L904-L917)
- [HIGH | Primary] **Never pass a filesystem name to a plain `Tree` as a `str`.**
  `Tree.process_label` runs `Text.from_markup` on strings, so a folder named `[b] Basement
  Survey` renders as ` Basement Survey`, silently losing the bracketed token (measured for
  `[b]`, `[i]`, `[u]`, `[link]`, `[red]`). Always construct `rich.text.Text`. Also note
  `process_label` keeps only the first line of any label.
  [`Tree.process_label`](https://github.com/Textualize/textual/blob/v8.2.8/src/textual/widgets/_tree.py#L847-L863)
- [HIGH | Primary] **The tree cursor is restored by line number, not node identity.**
  After rebuilding a subtree with a different child list, the cursor silently lands on a
  different node (measured: selected `delta`, got `echo`). Atlas must restore selection by
  its own stable key, exactly as `DirectoryTree._reload` hand-rolls path-based restore.
  [`_reload`](https://github.com/Textualize/textual/blob/v8.2.8/src/textual/widgets/_directory_tree.py#L250-L328)
- [HIGH | Primary] **Keep the existing worker pattern; it is already the recommended one.**
  Atlas already uses `@work(thread=True, exclusive=True, group=...)` plus `call_from_thread`
  and a generation guard. Textual's docs and the project lead both endorse posting messages
  from workers rather than touching the DOM from a thread.
  [Workers guide](https://textual.textualize.io/guide/workers/) ·
  [issue 6361](https://github.com/Textualize/textual/issues/6361)

## Implementation-prioritized shortlist

| Priority | Change | Why now | Suggested Atlas shape | Evidence |
|---|---|---|---|---|
| P0 | Plain `Tree[TreeItem]` over a hand-built model | The not-on-disk requirement is unreachable with `DirectoryTree`, and its stat cost fights the Drive mount | `Tree[TreeItem]` where `TreeItem` is an Atlas dataclass carrying path, kind (`on_disk` / `expected_missing` / `unfiled`), map section, and a `loaded` flag. Feed it from `atlas.core`, never from `iterdir` | [HIGH \| Primary] [`_populate_node`](https://github.com/Textualize/textual/blob/v8.2.8/src/textual/widgets/_directory_tree.py#L477-L491) · [`TreeNode.data`](https://github.com/Textualize/textual/blob/v8.2.8/src/textual/widgets/_tree.py#L94-L121) · measured ghost-node wipe |
| P0 | Lazy populate on `Tree.NodeExpanded`, guarded by a per-node `loaded` flag | Walking a studio drive eagerly stalls the loop and hydrates Drive placeholders | Handle `Tree.NodeExpanded`, return early if `node.data.loaded`, set the flag, dispatch a thread worker keyed to that node, populate on the message it posts back | [HIGH \| Primary] [`_add_to_load_queue`](https://github.com/Textualize/textual/blob/v8.2.8/src/textual/widgets/_directory_tree.py#L187-L204) · measured probe B (no duplicate children across collapse and re-expand) |
| P0 | List children through `atlas.core.scan.list_entries`, not `pathlib` | `os.scandir` gives name and directory-ness with no extra syscall on Windows; `Path.is_dir()` is a stat each time | Reuse the existing `Entry(name, is_dir)` dirent tuple. Never call `Path.resolve()` on a Drive path in the hot loop | [HIGH \| Primary] [`os.scandir`](https://docs.python.org/3/library/os.html#os.scandir) · measured 203 stats vs 0 |
| P0 | Override `render_label` for status glyphs and dimming | Tree nodes are not DOM nodes and cannot be styled with CSS selectors; `render_label` is the maintainer-endorsed route | Compose `Text` from a component style per node kind. Register Atlas component classes on the subclass so the token layer stays in CSS | [HIGH \| Primary] [davep, discussion 3802](https://github.com/Textualize/textual/discussions/3802) · [`render_label`](https://github.com/Textualize/textual/blob/v8.2.8/src/textual/widgets/_tree.py#L877-L902) |
| P0 | Build every label as `Text`, never `str` | Real project folder names containing `[b]`, `[i]`, `[u]`, `[link]`, `[red]` are silently mangled | Construct `Text` in the label builder; add a regression test using a folder name with a bracketed token | [HIGH \| Primary] measured probe E2 · [`process_label`](https://github.com/Textualize/textual/blob/v8.2.8/src/textual/widgets/_tree.py#L847-L863) |
| P1 | Override `get_label_width` | Cheapest available scale win, and the source docstring invites it | Return icon width plus `len(node.label.plain)` instead of rendering the label to measure it | [HIGH \| Primary] measured 25.4ms to 6.4ms at 5000 nodes · [`get_label_width`](https://github.com/Textualize/textual/blob/v8.2.8/src/textual/widgets/_tree.py#L904-L917) |
| P1 | Own the selection key; restore by path after any refresh | Cursor restore is positional and fails silently when the child list changes | Keep `selected_path: Path`. After a repopulate, force the line model, look the node up in an Atlas-maintained `dict[Path, TreeNode]`, then `move_cursor` | [HIGH \| Primary] measured probe M · [`_reload`](https://github.com/Textualize/textual/blob/v8.2.8/src/textual/widgets/_directory_tree.py#L250-L328) · [PR 5362 still open](https://github.com/Textualize/textual/pull/5362) |
| P1 | Give the tree its own worker group and a per-node generation guard | `exclusive=True` cancels every worker in the same group on that node, and `group` defaults to `"default"` | `@work(thread=True, group="tree-load", exit_on_error=False)`. Do not mark per-node loads `exclusive`, or expanding a second folder cancels the first | [HIGH \| Primary] [`add_worker`](https://github.com/Textualize/textual/blob/v8.2.8/src/textual/worker_manager.py#L65-L80) · [`_loader` uses `group="_loader"`](https://github.com/Textualize/textual/blob/v8.2.8/src/textual/widgets/_directory_tree.py#L529-L531) |
| P1 | Cooperative cancellation inside the loading thread | Cancelling a thread worker does not stop the thread; it only sets a flag | Poll `get_current_worker().is_cancelled` inside the scan loop, as `_directory_content` does. `Worker.cancelled_event` is a `threading.Event` if a blocking wait is needed | [HIGH \| Primary] [Workers guide](https://textual.textualize.io/guide/workers/) · [`Worker.cancel`](https://github.com/Textualize/textual/blob/v8.2.8/src/textual/worker.py#L416-L421) · measured probe F |
| P1 | Do not bind or expose expand-all on a lazy tree | `expand_all()` posts one `NodeExpanded` per descendant, which becomes a load storm | Measured 201 `NodeExpanded` messages from a single `expand_all()` on 201 nodes. Remove or re-bind `shift+space`, which is also unreachable in practice | [HIGH \| Primary] measured probe H · [`_expand`](https://github.com/Textualize/textual/blob/v8.2.8/src/textual/widgets/_tree.py#L249-L260) · [issue 5903](https://github.com/Textualize/textual/issues/5903) |
| P1 | Select newly added nodes after a refresh, not in the same cycle | Open issue 3547 still reproduces on 8.2.8: `select_node` on a just-added node lands the cursor on the root | Use `call_after_refresh(tree.select_node, node)`, or force the line model first. Both verified working | [HIGH \| Primary] [issue 3547](https://github.com/Textualize/textual/issues/3547) · measured probe J |
| P2 | Give the tree pane an explicit height and use `Widget.loading` | A `Tree` inside a non-scrolling container can silently truncate its node list; loading state is free | Set an explicit height or `1fr` on a scrolling parent. Set `tree.loading = True` while the first level loads, matching the existing table pattern | [MEDIUM \| Primary] [issue 4805](https://github.com/Textualize/textual/issues/4805) · [loading indicator](https://textual.textualize.io/guide/widgets/#loading-indicator) |
| P2 | Reuse `Tree.ICON_NODE` / `ICON_NODE_EXPANDED` for the glyph vocabulary | Class-level constants are the supported customization point, no rendering override needed | Override on the Atlas subclass. `DirectoryTree` adds `ICON_FILE` the same way | [HIGH \| Primary] [`ICON_NODE`](https://github.com/Textualize/textual/blob/v8.2.8/src/textual/widgets/_tree.py#L519-L522) |

## Findings

### Tree and TreeNode API at 8.2.8

- [HIGH | Primary] `Tree` is generic over its node payload: `Tree(label, data=None, ...)` and
  `Tree[TreeDataType]`. `TreeNode.data` is a plain public attribute holding an arbitrary
  value, which is the supported way to attach per-node state. `DirectoryTree` is simply
  `Tree[DirEntry]`.
  [`TreeNode.__init__`](https://github.com/Textualize/textual/blob/v8.2.8/src/textual/widgets/_tree.py#L94-L121) ·
  [Tree widget docs](https://textual.textualize.io/widgets/tree/)
- [HIGH | Primary] Node construction: `TreeNode.add(label, data=None, *, before=None,
  after=None, expand=False, allow_expand=True)` and `add_leaf(...)`. `before`/`after` accept
  an index or a sibling node; supplying both raises `AddNodeError`. `allow_expand` is a
  writable property, so a node can become expandable after the fact.
  [`TreeNode.add`](https://github.com/Textualize/textual/blob/v8.2.8/src/textual/widgets/_tree.py#L359-L434)
- [HIGH | Primary] Removal: `TreeNode.remove()` (raises `RemoveRootError` on the root),
  `TreeNode.remove_children()`, `Tree.clear()`, `Tree.reset(label, data)`.
  [`_tree.py` L472-L513](https://github.com/Textualize/textual/blob/v8.2.8/src/textual/widgets/_tree.py#L472-L513)
- [HIGH | Primary] Four messages, each carrying `.node` and a `.control` property:
  `Tree.NodeExpanded`, `NodeCollapsed`, `NodeHighlighted`, `NodeSelected`. Handler names are
  `on_tree_node_expanded` and friends.
  [`_tree.py` L689-L755](https://github.com/Textualize/textual/blob/v8.2.8/src/textual/widgets/_tree.py#L689-L755)
- [HIGH | Primary] Programmatic navigation: `move_cursor(node, animate=False)`,
  `move_cursor_to_line(line)`, `select_node(node)` (moves the cursor **and** posts
  `NodeSelected`), `unselect()`, `scroll_to_node`, `scroll_to_line`, plus lookups
  `get_node_at_line` and `get_node_by_id`.
  [`_tree.py` L962-L1050](https://github.com/Textualize/textual/blob/v8.2.8/src/textual/widgets/_tree.py#L962-L1050)
- [HIGH | Primary] `auto_expand` defaults to `True`, so selecting an expandable node also
  toggles it. Set `auto_expand = False` if Atlas wants selection and expansion separated.
  [`_expand_node_on_select`](https://github.com/Textualize/textual/blob/v8.2.8/src/textual/widgets/_tree.py#L1012-L1017)
- [HIGH | Primary] Styling hooks: component classes `tree--cursor`, `tree--guides`,
  `tree--guides-hover`, `tree--guides-selected`, `tree--highlight`, `tree--highlight-line`,
  `tree--label`; reactives `show_root`, `show_guides`, `guide_depth` (clamped 2-10),
  `center_scroll`; class constants `ICON_NODE`, `ICON_NODE_EXPANDED`, and the `LINES` guide
  character sets (`default`, `bold`, `double`).
  [`_tree.py` L519-L687](https://github.com/Textualize/textual/blob/v8.2.8/src/textual/widgets/_tree.py#L519-L687)
- [HIGH | Primary] There is **no** re-parent or move API on `TreeNode`; the public surface is
  `add`, `add_leaf`, `expand*`, `collapse*`, `toggle*`, `set_label`, `remove`,
  `remove_children`, `refresh`, plus read-only navigation properties. Re-parenting is an open
  Ideas request with no maintainer commitment. This matters for Atlas because conform
  relocations move folders: the tree must remove and re-add, or repopulate the subtree.
  [enumerated from 8.2.8 at runtime] · [discussion 6133](https://github.com/Textualize/textual/discussions/6133)
- [HIGH | Primary] There is no built-in "find node by data". A PR proposing it has been open
  and unmerged since 2024-12-08. Atlas must maintain its own `dict[Path, TreeNode]` index.
  [PR 5362](https://github.com/Textualize/textual/pull/5362)

### Per-node data and custom label rendering

- [HIGH | Primary] `render_label(node, base_style, style) -> Text` is the documented override
  for per-node appearance. `DirectoryTree` uses it to prefix an icon, apply
  `directory-tree--folder` / `--file` / `--hidden` component styles, and highlight the
  extension with `Text.highlight_regex`. That is a direct template for Atlas status rendering.
  [`DirectoryTree.render_label`](https://github.com/Textualize/textual/blob/v8.2.8/src/textual/widgets/_directory_tree.py#L389-L439)
- [HIGH | Primary] Textualize maintainer `davep`: "Nodes in a `Tree` aren't widgets, and so
  aren't part of the DOM, and as such can't be styled (directly) with CSS. Likely the best
  approach if you want custom highlighting is to inherit from `DirectoryTree` and extend
  `render_label`." This closes off any per-node CSS selector approach.
  [discussion 3802](https://github.com/Textualize/textual/discussions/3802)
- [HIGH | Primary] Use `get_component_rich_style("atlas-tree--missing", partial=True)` inside
  `render_label` to keep the Atlas palette in CSS rather than hard-coded in Python. This is
  how `DirectoryTree` reaches its own component classes.
  [`_directory_tree.py` L410-L437](https://github.com/Textualize/textual/blob/v8.2.8/src/textual/widgets/_directory_tree.py#L410-L437)
- [HIGH | Primary] `render_label` must return quickly. It is called once per rendered line
  and, through the default `get_label_width`, once per line on every full rebuild
  (measured: 5001 calls for a 5000-node build). Do no I/O in it.
- [HIGH | Primary-local, measured] Markup interception in a plain `Tree`, with the label
  passed as `str`:

  | Folder name | Rendered as `str` | Rendered as `Text` |
  |---|---|---|
  | `[2024] Alpha` | `[2024] Alpha` | `[2024] Alpha` |
  | `[DRAFT] Scheme A` | `[DRAFT] Scheme A` | `[DRAFT] Scheme A` |
  | `[b] Basement Survey` | ` Basement Survey` | `[b] Basement Survey` |
  | `[i] Interiors` | ` Interiors` | `[i] Interiors` |
  | `[u] Urban Design` | ` Urban Design` | `[u] Urban Design` |
  | `[link] Existing` | ` Existing` | `[link] Existing` |
  | `[red] Flagged` | ` Flagged` | `[red] Flagged` |

  Only names that happen to collide with a real Rich markup tag are damaged, which makes this
  a latent bug rather than an obvious one. `DirectoryTree` avoids it by overriding
  `process_label` to use `Text(label)`; a plain `Tree` does not.
  [`Tree.process_label`](https://github.com/Textualize/textual/blob/v8.2.8/src/textual/widgets/_tree.py#L847-L863) ·
  [`DirectoryTree.process_label`](https://github.com/Textualize/textual/blob/v8.2.8/src/textual/widgets/_directory_tree.py#L373-L387)
- [HIGH | Primary] Both `process_label` implementations end with `text_label.split()[0]`,
  keeping only the first line. A label containing a newline is silently truncated
  (measured: `"line one\nline two"` renders as `line one`). Tree labels are single-line by
  construction, so any two-line status idea is off the table.

### Lazy expansion

- [HIGH | Primary] `TreeNode.expand()` sets `_expanded = True` and posts `Tree.NodeExpanded`
  **before** any children exist. That is what makes populate-on-expand possible.
  [`_expand`](https://github.com/Textualize/textual/blob/v8.2.8/src/textual/widgets/_tree.py#L249-L270)
- [HIGH | Primary] `DirectoryTree` does not walk eagerly. Expansion enqueues the node
  (`_add_to_load_queue`), a single long-lived async worker (`_loader`, `group="_loader"`,
  `exclusive=True`) drains the queue, and each directory listing runs in a short-lived
  `@work(thread=True, exit_on_error=False)` worker. The `DirEntry.loaded` flag makes loading
  once-only per node.
  [`_add_to_load_queue`](https://github.com/Textualize/textual/blob/v8.2.8/src/textual/widgets/_directory_tree.py#L187-L204) ·
  [`_loader`](https://github.com/Textualize/textual/blob/v8.2.8/src/textual/widgets/_directory_tree.py#L529-L561) ·
  [`_load_directory`](https://github.com/Textualize/textual/blob/v8.2.8/src/textual/widgets/_directory_tree.py#L511-L527)
- [HIGH | Primary-local, measured] A plain `Tree` subclass with an
  `on_tree_node_expanded` handler and a `loaded` flag behaves correctly: children appear on
  first expand, and collapse plus re-expand does not duplicate them or re-run the populate.
- [HIGH | Primary] The queue exists because ordering matters. `_loader` holds
  `async with self.lock` for the whole populate so that a concurrent reload cannot interleave.
  `Widget.lock` is an `RLock` provided precisely for this: "Two different tasks might call
  methods on a widget at the same time, which might result in a race condition."
  [`Widget.lock`](https://github.com/Textualize/textual/blob/v8.2.8/src/textual/widget.py#L512-L518)
- [HIGH | Primary-local, measured] `expand_all()` posts one `NodeExpanded` per descendant
  (201 messages for 201 nodes). On a lazily loaded tree this becomes a recursive load of the
  entire drive. `Tree` binds it to `shift+space`, which Textual's own tracker notes no
  terminal appears to deliver, so the binding is largely dead but the action is still
  reachable through `toggle_all` and any custom binding.
  [`_expand`](https://github.com/Textualize/textual/blob/v8.2.8/src/textual/widgets/_tree.py#L249-L260) ·
  [issue 5903](https://github.com/Textualize/textual/issues/5903)

### DirectoryTree: what it gives, and what it costs

- [HIGH | Primary] Supported extension points are narrow and mostly subtractive:
  `filter_paths(paths)` (the only first-party example, and it filters hidden files),
  `render_label`, `process_label`, the `PATH` callable class var, and the `ICON_*` constants.
  Sort order, the `DirEntry` type, and the population routine are private.
  [filtered example](https://github.com/Textualize/textual/blob/v8.2.8/docs/examples/widgets/directory_tree_filtered.py) ·
  [`PATH`](https://github.com/Textualize/textual/blob/v8.2.8/src/textual/widgets/_directory_tree.py#L97-L98)
- [HIGH | Primary] `DirEntry` is a fixed dataclass of `path` and `loaded`, and it is
  constructed literally in four places (`__init__`, `watch_path`, `_reload`,
  `_populate_node`). There is no factory hook, so a richer per-node payload requires
  overriding all of them.
  [`DirEntry`](https://github.com/Textualize/textual/blob/v8.2.8/src/textual/widgets/_directory_tree.py#L23-L30)
- [HIGH | Primary-local, measured] Syscall cost for one load of a directory holding
  100 entries (10 directories, 90 files), counted by patching `pathlib.Path`:

  | Approach | `iterdir` | `is_dir` | `stat` | `resolve` | Path syscalls per entry |
  |---|---|---|---|---|---|
  | `DirectoryTree` load | 1 | 202 | 203 | 1 | ~4.06 |
  | `os.scandir(follow_symlinks=False)` | 1 | 0 | 0 | 0 | 0 |

  The `is_dir()` calls come from `_safe_is_dir`, invoked once in the sort key inside
  `_load_directory` and once per path in `_populate_node`. On Windows,
  `os.DirEntry.is_dir()` needs no system call because the information is already cached from
  the `scandir` call, which is exactly why `atlas.core.scan` was written that way.
  [`_load_directory`](https://github.com/Textualize/textual/blob/v8.2.8/src/textual/widgets/_directory_tree.py#L511-L527) ·
  [`os.scandir`](https://docs.python.org/3/library/os.html#os.scandir)
- [HIGH | Primary] `_load_directory` also calls `path.expanduser().resolve()` on every node
  it loads. `resolve()` touches the filesystem and follows links, which is additional work
  against a network mount and can rewrite a Drive path.
- [HIGH | Primary] `DirectoryTree` swallows the generic tree messages. Both
  `_on_tree_node_expanded` and `_on_tree_node_selected` call `event.stop()`, so a parent
  widget never sees `Tree.NodeExpanded` or `Tree.NodeSelected` from a `DirectoryTree`; it
  only sees `FileSelected` / `DirectorySelected`. Measured: a parent with all three handlers
  recorded 0, 0, and 1.
  [`_on_tree_node_expanded`](https://github.com/Textualize/textual/blob/v8.2.8/src/textual/widgets/_directory_tree.py#L563-L585)
- [HIGH | Primary] Error handling is silent by design. `_safe_is_dir` catches `OSError` and
  returns `False`, so a permission-denied directory renders as a file; the source comment
  concedes "A possible improvement in here could be to have a third state which is
  'unknown'". `_directory_content` catches `OSError` and yields nothing, so an unreadable
  folder simply appears empty. Atlas needs a real error state, which means owning this code.
  [`_safe_is_dir`](https://github.com/Textualize/textual/blob/v8.2.8/src/textual/widgets/_directory_tree.py#L456-L475)
- [HIGH | Primary] What is genuinely worth stealing: the load queue, the once-only `loaded`
  flag, the `async with self.lock` discipline, cursor preservation across a populate, and the
  path-based selection restore in `_reload`.

### Not-on-disk nodes

- [HIGH | Primary-local, measured] Injecting a node for a path that does not exist into a
  `DirectoryTree` appears to work, then silently loses the node: it survives the immediate
  add, but `reload_node(root)` rebuilds the child list from `iterdir()` and the injected node
  is gone. The same happens to a child ghost when its parent is loaded again. This is
  structural, not a bug: `_populate_node` starts with `node.remove_children()`.
- [HIGH | Primary] `filter_paths` cannot help, because it receives only paths that
  `iterdir()` already produced and returns a subset.
  [`filter_paths`](https://github.com/Textualize/textual/blob/v8.2.8/src/textual/widgets/_directory_tree.py#L441-L454)
- [HIGH | Primary] Conclusion: the "map expects it, disk lacks it" requirement forces a plain
  `Tree` with an Atlas-owned model. The children of a node are then the union of what
  `atlas.core.scan` found and what the drive map expects, with node kind carried in
  `TreeNode.data` and expressed through `render_label`. This also keeps the drive map as the
  only folder-structure brain, which the Atlas map requires.

### Virtualization and scale

- [HIGH | Primary] `Tree` extends `ScrollView` and implements `render_line(y)`, so only lines
  inside the viewport are rendered, and each rendered line is memoized in an `LRUCache` keyed
  on line number, hover, width, and per-node update counters. The cache starts at 1024
  entries and grows on resize.
  [`_render_line`](https://github.com/Textualize/textual/blob/v8.2.8/src/textual/widgets/_tree.py#L1314-L1439)
- [HIGH | Primary-local, measured] Nested tree, fanout 4, everything expanded, 132x38:

  | Expanded nodes | Full `_build()` | Cold viewport render | Warm re-render | Strips rendered |
  |---|---|---|---|---|
  | 500 | 2.0ms | 4.4ms | 0.0ms | 38 |
  | 2000 | 9.9ms | 4.3ms | 0.0ms | 38 |
  | 5000 | 20.5ms | 4.0ms | 0.0ms | 38 |
  | 5000 (flat, one level) | 29.0ms | 5.0ms | 0.1ms | 38 |

  Render cost is flat in node count. Rebuild cost is linear.
- [HIGH | Primary-local, measured] `_build()` calls `render_label` once per line (5001 calls
  for 5000 nodes) purely to measure label width, and computes `max()` across all of them to
  set `virtual_size`. Overriding `get_label_width` with a cheap arithmetic version cut the
  median full rebuild at 5000 nodes from 25.4ms to 6.4ms.
- [HIGH | Primary-local, measured] Mutations are cheap; rebuilds are not, and rebuilds are
  deferred. 100 individual `add()` calls into an existing 5000-node tree cost 1.3ms in
  total, followed by **one** rebuild of 27.5ms, not 100 rebuilds. `_invalidate()` only clears
  caches; `_build()` runs lazily when `_tree_lines` is next read, including from `_on_idle`.
  So bulk-populate freely, but expect one 20-30ms hitch per idle cycle in which anything
  changed. A collapse plus rebuild measured 17.2ms.
  [`_on_idle`](https://github.com/Textualize/textual/blob/v8.2.8/src/textual/widgets/_tree.py#L1246-L1250)
- [HIGH | Primary] Practical consequence for Atlas: keep the number of *simultaneously
  expanded* nodes low. Collapsed subtrees cost nothing in `_build`, because it only recurses
  into `node._expanded` children. A drive with thousands of files is fine as long as the user
  is not expanded into all of it at once, which is another reason not to offer expand-all.
- [MEDIUM | Primary] Tree nodes are not widgets and not part of the DOM, so a 5000-node tree
  is still one DOM node. Textual's known O(n)-descendant style-refresh behavior on focus,
  hover, and class changes therefore does not scale with tree size here.
  [davep, discussion 3802](https://github.com/Textualize/textual/discussions/3802) ·
  [issue 6524](https://github.com/Textualize/textual/issues/6524)
- [MEDIUM | Primary] The historical "tree is slow with thousands of nodes" report is from the
  pre-`Tree` era. Will McGugan on issue 767: "The tree control is slow with a large number of
  elements because it uses Rich's tree control and re-renders when you make changes (even
  hovering). We're planning an update which uses a new API to do more efficient updates."
  That update is the current `Tree`; the issue is closed as completed. Do not treat that
  report as evidence against `Tree` at 8.2.8.
  [issue 767](https://github.com/Textualize/textual/issues/767)
- [MEDIUM | Primary] A `Tree` inside a container that does not scroll can silently display
  only part of its nodes. The reported case was `TabbedContent` inside a `Container` with a
  default height of `1fr`. Give the tree pane an explicit height or a scrolling parent, and
  assert node counts in tests rather than trusting a snapshot.
  [issue 4805](https://github.com/Textualize/textual/issues/4805)

### Filesystem work off the event loop

- [HIGH | Primary] `@work(thread=True)` is required for blocking functions; the decorator
  raises `WorkerDeclarationError` on a non-async function without it. Parameters at 8.2.8:
  `name`, `group` (default `"default"`), `exit_on_error` (default `True`), `exclusive`
  (default `False`), `description`, `thread`.
  [`_work_decorator.py`](https://github.com/Textualize/textual/blob/v8.2.8/src/textual/_work_decorator.py#L72-L100)
- [HIGH | Primary] `exclusive=True` cancels every worker sharing that node **and** group.
  Since `group` defaults to `"default"`, an unqualified `@work(exclusive=True)` will cancel
  unrelated workers on the same widget. `DirectoryTree` avoids this by naming its group
  `"_loader"`. Atlas already names its groups (`scan`, `operation`, `prepare`); the tree
  needs its own.
  [`add_worker`](https://github.com/Textualize/textual/blob/v8.2.8/src/textual/worker_manager.py#L65-L80)
- [HIGH | Primary] Per-node lazy loads should **not** be exclusive. Expanding a second folder
  while the first is still listing would cancel the first. Use a shared non-exclusive group
  and discard stale results by generation, which is the pattern Atlas already applies to
  scans.
- [HIGH | Primary] Thread cancellation is cooperative. `Worker.cancel()` sets `_cancelled`,
  cancels the asyncio task, and sets `cancelled_event`, but the thread body keeps running
  until it checks. Textual's guide states it plainly: "you can't cancel threads in the same
  way as coroutines, but you _can_ manually check if the worker was cancelled."
  [Workers guide](https://textual.textualize.io/guide/workers/) ·
  [`Worker.cancel`](https://github.com/Textualize/textual/blob/v8.2.8/src/textual/worker.py#L416-L421)
- [HIGH | Primary-local, measured] Confirmed: after `cancel()`, `worker.is_cancelled` is
  `True` immediately and the state is `CANCELLED`, but the thread kept executing until its
  own `is_cancelled` check fired. `Worker.cancelled_event` is a `threading.Event`, so a
  blocking wait with a timeout is available inside the thread.
- [HIGH | Primary] `_directory_content` is the reference shape: iterate, and `break` on
  `worker.is_cancelled` each iteration.
  [`_directory_content`](https://github.com/Textualize/textual/blob/v8.2.8/src/textual/widgets/_directory_tree.py#L493-L509)
- [HIGH | Primary] UI hand-back. Textual: "You should avoid calling methods on your UI
  directly from a threaded worker, or setting reactive variables." Use `call_from_thread`, or
  `post_message`, which is "thread-safe" and preferred "if your worker needs to make multiple
  updates to the UI".
  [Workers guide](https://textual.textualize.io/guide/workers/) ·
  [`App.call_from_thread`](https://github.com/Textualize/textual/blob/v8.2.8/src/textual/app.py#L1788-L1816)
- [HIGH | Primary] Will McGugan, closing issue 6361 on 2026-02-16: "Workers are intended to
  live for the lifetime of the widgets, not its DOM. If you update the DOM directly as you
  are doing, you will have to ensure that the worker is stopped in time, or be defensive
  about getting DOM elements." He lists preferred alternatives including "Send messages from
  the worker" and "Update a reactive, and use `data_bind`".
  [issue 6361](https://github.com/Textualize/textual/issues/6361)
- [HIGH | Primary] `exit_on_error` defaults to `True`, meaning an unhandled exception in a
  worker exits the app. Every filesystem worker should set `exit_on_error=False`, as
  `_load_directory` and the existing Atlas workers already do.
- [MEDIUM | Primary] Thread workers run on asyncio's default executor
  (`loop.run_in_executor(None, ...)`), whose worker count is `min(32, cpu_count + 4)` (28 on
  this machine). Many concurrent expansions against a high-latency mount will queue there,
  and that pool is shared with anything else using `asyncio.to_thread`. Bound concurrent
  directory loads rather than firing one worker per expanded node without limit.
  [`_run_threaded`](https://github.com/Textualize/textual/blob/v8.2.8/src/textual/worker.py#L284-L326)
- [HIGH | Primary] Widget-level `loading` is a reactive that swaps in a `LoadingIndicator`,
  and `Tree` inherits it. Use it for the first-level load; use per-node placeholder children
  for deeper ones, since `loading` covers the whole widget.
  [loading indicator](https://textual.textualize.io/guide/widgets/#loading-indicator)

### Selection, cursor, and refresh identity

- [HIGH | Primary-local, measured] Open issue 3547 still reproduces on 8.2.8. Calling
  `select_node` on a node added in the same update cycle leaves the cursor on the root,
  because the new node's `_line` is still `-1` until `_build()` runs. Two fixes verified:
  read `tree._tree_lines` first to force the rebuild, or schedule the selection with
  `call_after_refresh`. The second is the public API and should be preferred.
  [issue 3547](https://github.com/Textualize/textual/issues/3547)
- [HIGH | Primary-local, measured] Cursor restoration after a subtree rebuild is positional,
  not identity-based:

  | Rebuild | Selected before | Cursor after |
  |---|---|---|
  | identical children | `delta` @ line 5 | `delta` @ line 5 |
  | one sibling removed above the cursor | `delta` @ line 5 | `echo` @ line 5 |
  | the selected item deleted | `delta` @ line 5 | `echo` @ line 5 |
  | subtree shrinks below the cursor line | `delta` @ line 5 | `alpha` @ line 2 |

  The cursor never reports an error; it just points somewhere else. Any Atlas action bound to
  the cursor after a refresh must re-resolve the selection from a stable key first.
  `_build()` reassigns `cursor_line` from the stale node's cached `_line`, which is why the
  first row appears to work.
  [`_build`](https://github.com/Textualize/textual/blob/v8.2.8/src/textual/widgets/_tree.py#L1287-L1298)
- [HIGH | Primary] First-party code hand-rolls exactly this restore. `DirectoryTree._reload`
  records the expanded paths and the highlighted path before resetting, then walks the
  rebuilt tree to find the same path, falling back to the nearest surviving parent. Atlas
  should implement the same policy over its own keys.
  [`_reload`](https://github.com/Textualize/textual/blob/v8.2.8/src/textual/widgets/_directory_tree.py#L250-L328)

### Deprecations, renames, and what online examples get wrong

- [HIGH | Primary] `TreeControl` no longer exists; `Tree` replaced it. Any example using
  `TreeControl` predates the rewrite and is unusable.
  [CHANGELOG](https://github.com/Textualize/textual/blob/main/CHANGELOG.md)
- [HIGH | Primary] Import paths moved and are easy to get wrong:
  - `Tree`, `DirectoryTree` come from `textual.widgets`.
  - `TreeNode`, `NodeID`, `TreeDataType`, `AddNodeError`, `RemoveRootError`, `UnknownNodeID`
    come from `textual.widgets.tree`. `TreeNode` has not been importable from
    `textual.widgets` since the 1637 change.
  - `DirEntry` comes from `textual.widgets.directory_tree`.
  - `RemoveRootError` and `UnknownNodeID` are module-level, not class attributes;
    `Tree.UnknownNodeID` and `TreeNode.RemoveRootError` were moved out.
  [verified against 8.2.8 re-export modules] ·
  [CHANGELOG](https://github.com/Textualize/textual/blob/main/CHANGELOG.md)
- [HIGH | Primary] `DirectoryTree.load_directory` was renamed to the private
  `_load_directory`. Examples that override `load_directory` now silently do nothing.
  Similarly `Tree.refresh_line` became internal.
- [HIGH | Primary] `Tree` and `DirectoryTree` messages no longer accept a `tree` parameter;
  use `event.node.tree` or the `control` property.
- [HIGH | Primary] `DirectoryTree.FileSelected.path` is always a `Path`, never a `str`.
- [HIGH | Primary] `NodeSelected` is now posted **before** `NodeExpanded`. Any ordering
  assumption from older examples is inverted.
- [HIGH | Primary] `DirectoryTree` no longer auto-selects the first node.
- [HIGH | Primary] The one breaking rename inside 8.0.0 is unrelated to trees but will bite
  anyone porting an older app: `Select.BLANK` became `Select.NULL`. 8.0.0 also stopped making
  dismissal of a non-active screen a no-op, and added a 50ms screen-switch delay.
  [CHANGELOG 8.0.0](https://github.com/Textualize/textual/blob/main/CHANGELOG.md)
- [HIGH | Primary] Within the 8.x line the tree work was maintenance, not API change: 8.0.1
  "`DirectoryTree` runs more operations in a thread to avoid micro-freezes" and 8.0.2 "Fixed
  issues with Directory Tree". Nothing between 8.0.0 and 8.2.8 changed the `Tree` or
  `DirectoryTree` public API, so 8.2.8 examples written for any 8.x are safe.
- [MEDIUM | Primary] `Tree.add_json` exists and is easy to mistake for a general model
  loader. It is a JSON pretty-printer that sets labels with markup and sets `allow_expand`
  itself; it is not a route to a domain tree.
  [`add_json`](https://github.com/Textualize/textual/blob/v8.2.8/src/textual/widgets/_tree.py#L791-L835)

## Contradictions and hidden variables

- [HIGH] **"DirectoryTree is the right widget for a filesystem tree" versus "DirectoryTree
  cannot show what is missing."** Split by *requirement*, not by version. For a pure
  disk-mirror browser `DirectoryTree` is correct and davep recommends it. Atlas needs union
  semantics over disk and drive map, which `_populate_node` structurally forbids. The
  requirement decides, and it decides against `DirectoryTree`.
- [HIGH] **"Textual trees are slow with thousands of nodes" versus measured flat render
  cost.** Split by *version*. The slowness report is issue 767 from 2022 against
  `TreeControl`, which re-rendered through Rich on every change. The current `Tree` renders
  only visible lines. At 8.2.8 the cost that remains is `_build()`, which is linear in
  *expanded* nodes, not total nodes.
- [HIGH] **"Cancel the worker when the user collapses or navigates away" versus "the thread
  keeps running".** Split by *worker kind*. Async workers are cancelled by the event loop;
  thread workers only observe a flag. Both are true; the code must poll.
- [MEDIUM] **"Use `exclusive=True` so stale results cannot land" versus "per-node loads must
  not cancel each other".** Split by *scope of the operation*. Exclusive is right for a
  whole-drive rescan, where only the latest matters, and wrong for concurrent per-node
  expansion. Group naming plus a generation guard resolves it; exclusivity alone does not.
- [MEDIUM] **`str` labels are fine in every example, yet mangle real folder names.** Split by
  *input source*. Hand-written example labels never collide with Rich markup tags; real
  studio folder names sometimes do. The examples are not wrong, they are unrepresentative.
- [LOW] **Community examples subclass `DirectoryTree` for S3, GCS and other remote stores via
  `universal_pathlib` and the `PATH` class var.** This suggests the widget is filesystem
  agnostic. It is path-object agnostic, but the syscall pattern is unchanged, so latency per
  entry still multiplies by roughly two stats. Not evidence that it suits a Drive mount.
  [discussion 1719](https://github.com/Textualize/textual/discussions/1719) ·
  [issue 5648](https://github.com/Textualize/textual/issues/5648)

## Survivorship-bias sweep

- [HIGH | Primary] **`DirectoryTree` extension requests that were declined or never landed.**
  Will McGugan on above-root navigation: "I don't think we want to include a way of
  navigating beyond the root. I feel that should be provided by another widget that embeds
  DirectoryTree." The maintainer position is that `DirectoryTree` should be *embedded and
  worked around*, not extended. That is the strongest single argument for owning the model.
  [issue 2056](https://github.com/Textualize/textual/issues/2056)
- [HIGH | Primary] **Documented community workaround for changing the root: throw the widget
  away.** davep, in the same thread: remove the `DirectoryTree` and mount a fresh one with the
  new root. A widget whose supported reconfiguration story is "replace it" is a poor base
  class for a long-lived pane.
  [issue 2056](https://github.com/Textualize/textual/issues/2056)
- [HIGH | Primary] **Customization requests routed to private methods.** Natural sort order
  for `DirectoryTree` has no supported hook; the working community answer overrides the
  private `_load_directory`. Unmerged, and private-API dependent.
  [discussion 6129](https://github.com/Textualize/textual/discussions/6129)
- [HIGH | Primary] **Node re-parenting has been requested and not implemented.** An Ideas
  post with a community-drafted `TreeNode.move` has sat since 2025-09-25 with no maintainer
  commitment; 8.2.8 has no such method. Plan on remove-and-re-add for relocations.
  [discussion 6133](https://github.com/Textualize/textual/discussions/6133)
- [HIGH | Primary] **Find-node-by-data has been proposed and not merged since 2024-12-08.**
  Applications are expected to maintain their own index.
  [PR 5362](https://github.com/Textualize/textual/pull/5362)
- [HIGH | Primary] **Per-node CSS styling is a dead end that people keep trying.** It fails
  because tree nodes are not DOM nodes. The maintainer answer is always `render_label`.
  [discussion 3802](https://github.com/Textualize/textual/discussions/3802)
- [HIGH | Primary] **Direct DOM updates from workers were explicitly discouraged in the 8.0
  window**, with four named alternatives, after a user hit a teardown race.
  [issue 6361](https://github.com/Textualize/textual/issues/6361)
- [MEDIUM | Primary] **An unresolved performance report that will not be fixed soon.**
  `update_node_styles` walking all descendants on every focus, hover and class change was
  reported against 8.2.5 and the accompanying PR was closed under the project's AI policy,
  not on technical grounds. It remains in 8.2.8. It does not scale with tree node count, but
  it does scale with the number of real widgets in the console, so keep the surrounding
  layout shallow.
  [issue 6524](https://github.com/Textualize/textual/issues/6524)
- [HIGH | Primary] **No abandonment evidence found against `Tree` itself.** No open issue
  reports the current `Tree` failing at scale, and there is no maintainer statement
  discouraging its use with an application-owned model. The evidence points at
  `DirectoryTree` as the constrained component, not `Tree`.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---|---|---|---|
| Rendering a large tree without redrawing everything | A custom virtualized list, or manual scroll-window bookkeeping | `Tree`, which extends `ScrollView` and implements `render_line` with an LRU line cache | Measured 38 strips rendered whether the model holds 500 or 5000 lines; warm re-render 0.0-0.1ms |
| Running a directory listing without freezing the UI | `threading.Thread` plus a hand-rolled result queue | `@work(thread=True, exit_on_error=False)` with `get_current_worker().is_cancelled` | Integrates with Textual's worker lifecycle, state messages, and app shutdown; the guide is explicit that UI calls from raw threads are unsafe |
| Getting worker results back to the UI safely | A shared mutable buffer read by a timer | `post_message` for streams of updates, `call_from_thread` for single calls | Both are documented as the thread-safe routes; the project lead names "send messages from the worker" as a preferred pattern |
| Serializing a reload against in-flight expansions | An ad-hoc `asyncio.Lock` on the app | `Widget.lock`, which every widget already has | Provided for exactly this; `DirectoryTree._reload` and `_loader` both use it |
| Listing a directory with type information | `Path.iterdir()` then `Path.is_dir()` per entry | `os.scandir` with `follow_symlinks=False`, already wrapped as `atlas.core.scan.list_entries` | Measured 203 stat calls versus 0 for 100 entries; `DirEntry.is_dir()` needs no syscall on Windows |
| Per-node colour, glyphs and dimming | Building ANSI escapes or per-node widgets | Override `render_label` and reach component classes with `get_component_rich_style` | Maintainer-endorsed; keeps the palette in CSS for the planned Atlas token layer |
| An indeterminate busy state on the pane | A custom spinner widget | `Tree.loading = True`, inherited from `Widget` | Swaps in the built-in `LoadingIndicator`; already the pattern used for the project table |
| A tree-shaped diff between map and disk | A bespoke tree-diff renderer | The existing `atlas.core` report plus one node kind on `TreeNode.data` | The core already computes missing, drift, relocations, sweeps and unfiled; the tree should present that, not recompute it |

## Validation queue

- [LOW | Implementation-time validation] Re-run the scale probe against a real Google Shared
  Drive project rather than local NTFS, and record wall-clock time for first expansion of a
  cold folder. Local timings here bound CPU cost only; Drive latency is per syscall and is
  the term that dominates.
- [LOW | Implementation-time validation] Confirm the realistic upper bound on
  simultaneously expanded nodes for a studio project. If a plausible session exceeds roughly
  2000 expanded nodes, add the `get_label_width` override before shipping rather than after.
- [LOW | Implementation-time validation] Decide and test the concurrency cap for parallel
  directory loads against the shared default executor. Verify behavior when a user expands
  several folders quickly on a cold mount.
- [LOW | Implementation-time validation] Verify cooperative cancellation actually fires
  promptly when a user collapses a node mid-load over Drive, where a single `scandir` may
  block for seconds and the flag is only checked between entries.
- [LOW | Implementation-time validation] Test a project folder whose name contains a Rich
  markup token (`[b]`, `[i]`, `[link]`, `[red]`) end to end, and add it to the fixture drive
  in `tests/conftest.py`.
- [LOW | Implementation-time validation] Verify the tree pane renders its full node list at
  132x38 and 80x24 inside the real Atlas layout, asserting node counts rather than relying on
  a snapshot, given the container-height truncation case in issue 4805.
- [LOW | Implementation-time validation] Confirm `render_label` glyph choices render in the
  studio's actual terminal. The `DirectoryTree` defaults are emoji, which are double-width and
  inconsistent across terminals; the Atlas glyph vocabulary should be validated before it is
  locked into the token layer.
- [LOW | Implementation-time validation] Verify permission-denied and offline-placeholder
  folders produce a visible Atlas error state, since the `DirectoryTree` precedent for both is
  silent.
- [LOW | Version validation] The claims here are pinned to 8.2.8 and verified byte-identical
  to the `v8.2.8` tag. If the `textual>=8.2,<9` floor is ever raised or a consumer resolves a
  different 8.x, re-check only the deprecation section; the API was stable across 8.0.0 to
  8.2.8.

## Source quality summary

- [HIGH | Primary] Textual 8.2.8 source, read locally and confirmed byte-identical to the
  `v8.2.8` tag: `_tree.py`, `_directory_tree.py`, `worker.py`, `worker_manager.py`,
  `_work_decorator.py`, `widget.py`, `app.py`.
- [HIGH | Primary-local] Measured behavior from probe scripts driving real widgets through
  `App.run_test()` under the Atlas venv on Python 3.12.13 / Windows 11. Covers scale timing,
  label markup, lazy expansion, event propagation, ghost nodes, syscall counts, worker
  cancellation, and cursor identity.
- [HIGH | Primary] Textual official docs: [Tree](https://textual.textualize.io/widgets/tree/),
  [DirectoryTree](https://textual.textualize.io/widgets/directory_tree/),
  [Workers](https://textual.textualize.io/guide/workers/),
  [widget loading](https://textual.textualize.io/guide/widgets/#loading-indicator).
- [HIGH | Primary] Textual first-party tracker and discussions, including maintainer
  statements from Will McGugan (issues 767, 2056, 6361) and davep (issues 2056; discussions
  2730, 3802), plus the project CHANGELOG.
- [HIGH | Primary] Python standard library documentation for
  [`os.scandir`](https://docs.python.org/3/library/os.html#os.scandir).
- [MEDIUM | Synthesis] The prioritized shortlist and the Atlas-specific shapes infer fit from
  the primary evidence plus the local constraints in `atlas.core.scan` and the Atlas map.
  Validate against the real drive before treating the ordering as settled.
