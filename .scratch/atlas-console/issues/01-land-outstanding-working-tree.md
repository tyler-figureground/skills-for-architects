# Land the outstanding Atlas working tree

Type: task
Status: open
Blocked by: -
Parent: ../map.md

## Question

Roughly thirty modified and untracked files sit in the working tree - the project
intake, shared contacts, and project/contact editing work - while `main` is ahead of
`origin/main` by one commit. `.agent/handoff/atlas-editing-plan.md` and
`.agent/handoff/atlas-project-intake-plan.md` both record that work as complete and
production-deployed, and `CONTEXT.md`, `docs/adr/0003-...`, and five new core modules
with their tests are part of it.

Every redesign diff from this map lands on top of that. Until it is resolved, no
review of this effort's changes is legible and no bisect is meaningful.

Decide and execute:

- Does the outstanding work get committed as-is, split into reviewable commits, or
  partially discarded?
- Does it get pushed, given `main` is already ahead by one?
- Do `.agent/` and `.impeccable/` belong in the repository or in `.gitignore`?
- Does `.scratch/` - this map - belong in the repository or ignored?

This is a task, not a decision about Atlas. It unblocks clean execution of every
ticket after it. Resolve by actually landing the tree, then record what was done and
the resulting commit range.
