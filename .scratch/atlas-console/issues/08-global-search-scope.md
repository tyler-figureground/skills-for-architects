# Global search scope

Type: grilling
Status: open
Blocked by: -
Parent: ../map.md

## Question

Global search is in scope: one keystroke, search across the drive, jump to the
result. What it searches is undecided.

Ticket 06 is now in and constrains this hard. Enumeration is the unit of cost and
Google shared drives are streaming-only, so any name search wider than the project
list is a walk of the whole drive over a network mount with no published latency
figure. `Path.rglob` is out - it suppresses every `OSError`, so a mount hiccup
would return a short result set with no error.

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
