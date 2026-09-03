# 4. Tree nodes carry a Filing State and a Load State, and missing folders are not nodes

Date: 2026-09-02

## Status

Accepted

## Context

Atlas is growing a navigable per-project folder tree. Every node has to be drawn
by `render_label`, because Textual tree nodes are not DOM nodes and take no CSS
(established by the ticket 05 research), so whatever a node "is" has to be a value
Python can read at render time. The same value drives the token layer, the `--json`
agent interface, and the actions offered on a node.

Atlas already has vocabulary for this at the *project* level. `ProjectReport`
carries `drift`, `relocations`, `sweeps`, `unfiled`, and `missing_control_plane`,
and `doctor` assigns each project one of `conform`, `drift`, `unfiled`, `stub`.
The TUI then relabels those four as `READY`, `ACTION`, `REVIEW`, `SETUP`. That is
already two vocabularies for one idea, and a per-node tree threatened to add a
third.

Three specific pressures shaped the decision:

1. A node can be several things at once in ways that a single flat enum handles
   badly. A folder the map accounts for can also be a folder Atlas failed to open.
   A folder nobody has filed can also be a folder nobody has expanded yet.
2. Enumeration can fail or come back incomplete. The ticket 12 measurement found
   two directories on the live studio drive that raise `FileNotFoundError` while
   their own parents list them, and Atlas currently reports one of them as an
   empty folder when it is not. "Empty" and "could not read" must never be the
   same rendering.
3. The tree was chosen as a filesystem mirror with unmet map expectations listed
   separately, not merged inline. A folder the map wants and disk lacks has no
   path to expand, no children, no actions except "create it", and no position in
   a sibling order that means anything. Making it a node forces every consumer of
   a node to special-case it.

## Decision

**A Tree Node is a thing that exists on disk.** A folder the map expects and disk
lacks is an unmet Expectation, listed beside the tree. It is not a node.

**Every Tree Node carries two orthogonal values.**

*Filing State* - what the map says about it. Exactly one of `Mapped`, `Drifted`,
`Misplaced`, `Loose`, `Unfiled`, resolved by the first map rule that matches in
the order conform already applies them: drift renames, then relocations, then
sweeps. `Unfiled` is the fallthrough.

*Load State* - what Atlas knows about its children, for folders only. One of
`Unread`, `Read`, `Unreadable`, `Partial`.

Emptiness is derived, not stored: a folder is empty when its Load State is `Read`
and it has no children. A folder that is `Unread`, `Unreadable`, or `Partial` is
never described as empty.

**Filing State maps onto exactly two things a person needs to know**, and the
rendering carries that rather than the raw state name:

| Filing State | Meaning to a person | Fill | Colour |
|---|---|---|---|
| Mapped | Filed correctly | solid | ready |
| Drifted / Misplaced / Loose | Atlas can fix this | hatched | action |
| Unfiled | You have to decide | hatched | review |

Solid versus hatched answers "is anything wrong here", and colour answers "can
Atlas handle it or is it mine". Someone who opens Atlas twice a month reads the
tree without a legend. The specific state name appears in the node's own label.

## Consequences

Node rendering keys on two small enums that a Python token table can index, which
is what `render_label` needs and what a Textual stylesheet could not have given us.

`--json` gains both fields per node. Consumers that only care whether something is
wrong can read Filing State; consumers that care whether the data is trustworthy
must read Load State, and are now able to.

`core.scan.list_entries` has to stop returning an empty tuple on `OSError`, because
`Unreadable` is now a state the model can express and the TUI is required to show.
That change is owned by its own ticket and is a breaking change to a core seam with
four existing callers.

The tree never shows a folder that is not there. Unmet Expectations get their own
list, which also means the "create the folders the map wants" action operates on
that list rather than on phantom tree nodes.

Adding a sixth Filing State later is cheap. Adding a third axis is not, and should
be resisted; if something does not fit, it is probably a property of the node
rather than a state of it.

We keep the existing project-level `conform` / `drift` / `unfiled` / `stub`
statuses unchanged. They answer a different question - how is this whole project
doing - and renaming them was not worth the churn. The overlap between `drift` the
project status and `Drifted` the Filing State is real and is the main cost of this
decision.
