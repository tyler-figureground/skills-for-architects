# Console layout and navigation model

Type: grilling
Status: open
Blocked by: -
Parent: ../map.md

## Question

The portfolio dashboard is out of scope, so the project list stays the landing
surface. That leaves the relationship between the list and the tree undecided.

The prototypes show both panes at once. That reads well at 132 columns and breaks
below roughly 100 - the current app already declares breakpoints at 100 and hides
its detail pane below that.

Resolve:

- Does the tree sit permanently beside the project list, or does Enter push into a
  full-width tree for one project with Escape returning?
- If responsive: what happens at each breakpoint, and does the model change or only
  the composition? A layout that changes navigation model by width is harder to
  build muscle memory against.
- Where do the dossier panel and search results live in whichever model wins - a
  third pane, a mode of the right pane, or an overlay?
- What is on screen at first paint, before a project is selected?
- Which pane holds focus on entry, and what does Tab cycle through?
- The current app has a filter input, a summary line, an operation line, and a
  footer. Which of those survive, and does the operation line stay a persistent row
  or become transient?

Both operators must be served: fast for daily portfolio work, legible for someone
who opens Atlas twice a month.
