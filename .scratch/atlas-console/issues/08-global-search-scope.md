# Global search scope

Type: grilling
Status: open
Blocked by: 06
Parent: ../map.md

## Question

Global search is in scope: one keystroke, search across the drive, jump to the
result. What it searches is undecided, and ticket 06 sets what is affordable.

Resolve:

- What is searchable: project names only, project names plus dossier facts, folder
  and file names across all projects, or file contents?
- Drive-wide, or scoped to the selected project with a widen key?
- Is it live-as-you-type or submit-then-results? Live search over a network mount is
  a different engineering problem than a submitted query.
- Does it need an index? If so, where does the index live, when is it built, and how
  does it go stale? An index file on the drive is shared state that other studio
  machines will also read.
- What does a result look like, and what does selecting one do - reveal in the tree,
  open the project, open the file?
- How does this relate to the existing `/` filter over the project list? Is that
  filter subsumed, kept alongside, or promoted into this?
- What happens with no results, with too many results, and while a slow search runs?
