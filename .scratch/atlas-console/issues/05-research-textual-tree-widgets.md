# Textual 8.2.8 tree widgets and lazy loading

Type: research
Status: resolved
Blocked by: -
Parent: ../map.md

## Question

Primary-source evidence for building the project folder tree on Textual 8.2.8, the
version this project is locked to (`textual>=8.2,<9`, resolved 8.2.8).

Answer, with direct citations to official docs, API reference, source, or release
notes - not blog posts:

- The `Tree` and `DirectoryTree` APIs at 8.2.8: node data, custom label rendering
  (Rich `Text` per node), expand and collapse events, programmatic selection, and
  how to attach arbitrary per-node state.
- Lazy expansion: the supported way to populate children only when a node expands,
  and whether `DirectoryTree` does this already or walks eagerly.
- `DirectoryTree` filtering and subclassing hooks - can it render nodes that do not
  exist on disk, which the not-on-disk requirement needs, or must a plain `Tree` be
  used with a hand-built model?
- Virtualization and scrolling behavior at a few thousand nodes.
- Doing filesystem work off the event loop: current guidance on `@work(thread=True)`,
  worker cancellation, and pushing results back to the UI safely.
- Anything deprecated, renamed, or behavior-changed between 8.x and the API surface
  most examples online assume.
- Negative evidence: known open issues against `Tree`/`DirectoryTree`, and any
  approach the maintainers have explicitly discouraged.

Capture as a confidence-tiered report under `docs/research/`, following the pattern
of `docs/research/atlas-tui-ux-evidence.md`. Do not create a branch - the working
tree is already loaded and ticket 01 owns landing it.

Do not expose repository code externally.

## Answer

Report: `docs/research/atlas-tree-widget-evidence.md` (uncommitted, no branch created).

Evidence base: Textual 8.2.8 source read locally and verified byte-identical to the
`v8.2.8` git tag, so every source citation is a stable permalink with exact line
numbers. Docs, CHANGELOG, and the first-party tracker on top of that. Plus measured
behavior from probe scripts driving real widgets through `App.run_test()` under the
Atlas venv (Python 3.12.13, Windows 11). No repository code left the machine.

Top conclusions:

1. **Build on plain `Tree`, not `DirectoryTree`.** Three independent blockers, each
   sufficient. `DirectoryTree._populate_node` calls `node.remove_children()` before
   repopulating from `iterdir()`, so a not-on-disk node is destroyed on the next load
   (measured: injected node gone after `reload_node`). `filter_paths` is the only
   additive-looking hook and it can only subtract. And `DirectoryTree` costs ~2.0
   `is_dir()` stats per directory entry per load (measured 202 `is_dir` / 203 `stat`
   for one load of a 100-entry directory) where `atlas.core.scan`'s `os.scandir` pays
   zero, which matters because the Drive mount hydrates placeholders on stat.

2. **Lazy expansion works and `DirectoryTree` is the pattern to copy, not inherit.**
   `expand()` posts `NodeExpanded` before children exist. Copy the load queue, the
   once-only `loaded` flag on `TreeNode.data`, `async with self.lock` around populate,
   and the path-based selection restore. Do not bind expand-all: measured 201
   `NodeExpanded` messages from one `expand_all()` on 201 nodes, which is a load storm.

3. **Scrolling is virtualized; rebuilding is not.** Measured 38 strips rendered whether
   the model holds 500 or 5000 lines, warm re-render 0.0-0.1ms. But `_build()` is linear
   in *expanded* nodes and calls `render_label` once per line: 20-30ms per full rebuild
   at 5000 expanded nodes, triggered by any mutation, resize, or style change. Cost is
   per idle cycle, not per mutation (100 adds = 1.3ms, then one 27.5ms rebuild).
   Overriding `get_label_width` cut the median rebuild from 25.4ms to 6.4ms.

4. **Two silent-corruption traps.** `Tree.process_label` runs `Text.from_markup` on
   `str` labels, so a folder named `[b] Basement Survey` renders as ` Basement Survey`
   (measured for `[b]`, `[i]`, `[u]`, `[link]`, `[red]`; `[2024]` and `[DRAFT]` survive,
   which makes it latent). Always pass `rich.text.Text`. And the tree cursor is restored
   by *line number*, not node identity: after a subtree rebuild with a different child
   list the cursor silently points at a different node (selected `delta`, got `echo`).
   Atlas must re-resolve selection from its own key after every refresh.

5. **Keep the existing worker shape, add a named group.** `@work(thread=True,
   exit_on_error=False)` with cooperative `worker.is_cancelled` polling, results handed
   back by `post_message` / `call_from_thread`. Per-node loads must **not** be
   `exclusive`, or expanding a second folder cancels the first; `exclusive` also cancels
   every worker sharing the default `group="default"` on that widget.

Negative evidence worth carrying forward: maintainers treat `DirectoryTree` as something
to embed and work around rather than extend (Will McGugan, issue 2056); per-node CSS
styling is impossible because tree nodes are not DOM nodes, `render_label` is the only
route (davep, discussion 3802); `TreeNode` has no re-parent API (discussion 6133 open)
and no find-by-data (PR 5362 open since 2024-12-08); open issue 3547 still reproduces on
8.2.8, so `select_node` on a just-added node lands on the root unless deferred with
`call_after_refresh`. No open issue reports the current `Tree` failing at scale; the old
"trees are slow" report (issue 767) is from the pre-`Tree` `TreeControl` era.

Verification run this session: `./scripts/lint.sh` passed (all checks). Four probe
scripts ran green against the pinned venv. No Atlas source was modified, so
`uv run pytest` was not re-run.

### Questions this raised that the map does not yet cover

- **Node kind vocabulary.** The tree needs a name for each state a node can be in
  (on disk and mapped, on disk and unfiled, mapped but missing, unreadable or
  permission-denied, not yet loaded). `/CONTEXT.md` has no term for these yet, and
  `render_label` plus the planned token layer both key off whatever it is called.
  This is a `/domain-modeling` ticket, and it blocks the token layer entry in
  "Not yet specified".
- **What a node expansion is allowed to cost.** The map fixes Drive latency as the
  performance reality but sets no budget. Lazy loading needs a stated ceiling before
  it can be tuned: how long a cold folder may take before the pane shows a loading
  state, and how many folders may load concurrently against a shared thread pool.
- **Relocation and the tree.** Conform moves folders, and `TreeNode` has no re-parent
  API. The map's "File-level action set" entry does not say whether an applied plan
  refreshes the whole subtree, patches it node by node, or invalidates the tree and
  makes the user re-expand. Selection restore policy depends on the answer.
- **Error state ownership.** `DirectoryTree` renders a permission-denied folder as a
  file and an unreadable folder as empty, both silently. The map lists "permission
  error" under "Tree states" but not who detects it: `atlas.core.scan.list_entries`
  currently swallows `OSError` and returns an empty tuple, so the TUI cannot tell
  "empty" from "unreadable" today. That is a core seam change, not a TUI one.
