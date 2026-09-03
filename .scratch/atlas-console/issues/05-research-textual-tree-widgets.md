# Textual 8.2.8 tree widgets and lazy loading

Type: research
Status: claimed
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
