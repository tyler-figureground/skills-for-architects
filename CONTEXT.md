# Domain Glossary

## Atlas Project Intake

**Project**  
An architecture engagement represented by one mapped project folder and one `PROJECT.md` dossier.

**Project Name**  
Human-facing name of the engagement. Required. Distinct from its folder name and address.

**Project Address**  
Required full US site address: physical numbered street, optional unit, city, state, and ZIP code. Distinct from any contact's mailing address. Never a PO box.

**Short Address**  
Street number plus street name and suffix from the Project Address. Excludes unit, city, state, and ZIP. Used in the project folder name.

**Description**  
Optional short qualifier appended to the project folder name. Distinct from Project Use Case.

**Project Use Case**  
Required classification of the engagement: Renovation, Addition, Renovation + Addition, Ground Up, Feasibility, Existing Conditions, Code Compliance, or Other. Other requires a custom label. Project Use Case is not an IBC occupancy or building use group.

**Contact**  
Reusable person in the firm's shared contact directory. Identified by a stable ID. Email is unique case-insensitively. A contact has required first name, last name, and email; phone, company, and mailing address are optional.

**Contact Mailing Address**  
Optional US correspondence address for a Contact. May use either a physical numbered street or a PO box. Distinct from Project Address.

**Billing Contact**  
Required Contact responsible for billing correspondence on a Project.

**Client Contact**  
Required Contact representing the client relationship on a Project. Defaults to the Billing Contact during intake but may be overridden.

**Contact Snapshot**  
Copy of a Contact's details stored in the Project dossier at creation or explicit Project edit. Preserves project history when the shared Contact later changes. Shared Contact edits never rewrite snapshots automatically.

**Project Update**  
Explicit correction of an existing Project's intake fields. Address or Description changes may derive a new folder name; Atlas previews and confirms that rename, rejects collisions, and updates the dossier and project index together.

## Atlas Project Tree

**Tree Node**
One folder or file that exists on disk inside a Project folder. Only things on
disk are Tree Nodes. A folder the drive map expects but disk lacks is an unmet
Expectation, not a Tree Node.

**Expectation**
A folder the drive map requires a Project to have. Met when a Tree Node exists at
that path; unmet otherwise. Unmet Expectations are listed beside the tree, never
drawn inside it.

**Filing State**
What the drive map says about a Tree Node that exists. Exactly one of Mapped,
Drifted, Misplaced, Loose, or Unfiled, decided by the first map rule that matches
in the order conform applies them. Distinct from Load State.

**Mapped**
Filing State of a Tree Node the drive map accounts for, at the path it occupies.
Nothing to do.

**Drifted**
Filing State of a Tree Node whose name the drive map renames to a canonical one.
Atlas can repair it without a human decision.

**Misplaced**
Filing State of a Tree Node the drive map relocates to a different path. Atlas can
repair it without a human decision.

**Loose**
Filing State of a file sitting at a Project root that the drive map files into a
target folder. Atlas can repair it without a human decision.

**Unfiled**
Filing State of a Tree Node the drive map knows nothing about. Atlas can never
repair it, because only a person can decide where it belongs or whether it should
exist.

**Load State**
What Atlas knows about a folder Tree Node's children. One of Unread, Read,
Unreadable, or Partial. Orthogonal to Filing State: a Mapped folder can be
Unreadable, and an Unfiled folder can be Unread.

**Unread**
Load State of a folder whose children have not been enumerated yet. The starting
state of every folder below the one in view.

**Read**
Load State of a folder whose children were enumerated completely.

**Unreadable**
Load State of a folder whose enumeration failed. Never presented as empty; an
empty folder and a folder Atlas could not open are different facts.

**Partial**
Load State of a folder whose enumeration returned an incomplete list, either
because a cap was reached or because the filesystem returned fewer entries than
exist. Never presented as complete.

**Empty Folder**
A folder Tree Node whose Load State is Read and which has no children of its own.
Only a Read folder can be known to be empty. Distinct from Fileless.

**Fileless**
A folder with no file anywhere beneath it, however deep. This is what Clean
removes, by rmdir cascade. A Fileless folder is often not an Empty Folder - it may
contain a chain of subfolders that themselves contain no files - and an Empty
Folder is always Fileless. The tree reports Empty; Clean acts on Fileless.

**Child Count**
The number of a folder Tree Node's own children, split into folders and files.
Free, because it is the length of the enumeration already held. Never recursive:
a recursive count is a walk of the whole subtree, and Atlas does not spend that to
draw a label.

---
title: "context-append.md"
date: 2026-09-03
generated_by: skills-for-architects
---


## Atlas Console Layout

**Region**
A named area of the console that can take focus, be collapsed, and be maximized.
Exactly three exist: the Project List, the Tree Region, and the Companion Region.
_Avoid_: pane, panel, sidebar.

**Project List**
The Region listing every Project on the mapped drive. The console's landing
surface: focus starts here, and the Selected Project is whichever row its cursor
rests on.

**Workspace**
The container holding one Project's Tree Region and Companion Region, under a
title carrying the Project Name. Not itself a Region - it takes no focus and
collapses only by collapsing what it holds.

**Tree Region**
The Region drawing the Tree Nodes of the Selected Project.

**Companion Region**
The Region under the Tree Region, showing one Companion Mode at a time. Under,
not beside: the console has rows to spend and columns it does not.

**Companion Mode**
One of the three things the Companion Region can show - unmet Expectations,
project health, or the dossier. Unmet Expectations is the default, because it is
the only one that has to be readable at the same time as the tree.

**Selected Project**
The Project the Project List cursor rests on, and therefore the Project the
Workspace draws. Distinct from a marked Project, which is a batch selection and
does not move the cursor.

**Split Composition**
The console arrangement showing the Project List and the Workspace side by side.
The arrangement at wide terminal widths.

**Single-Region Composition**
The console arrangement showing exactly one Region at a time, the others hidden
rather than shrunk. The arrangement at narrow terminal widths, and the common one
rather than the degraded one. The navigation model is identical in both
Compositions; only what is on screen differs.
---
title: "context-append-2.md"
date: 2026-09-03
generated_by: skills-for-architects
---


## Atlas Writes

**Plan**
The complete description of a set of writes, built in core, shown to a person
before anything happens, and applied only after they confirm it. Atlas has no
other way to change a drive.

**Action**
One write inside a Plan. Exactly one of Backfill (create a folder the drive map
expects), Rename (a Drifted Tree Node to its canonical name), Relocate (a
Misplaced Tree Node to its mapped path), or Sweep (a Loose file into its target
folder).

**Repair**
The single Action a Tree Node's Filing State earns: Drifted earns a Rename,
Misplaced a Relocate, Loose a Sweep. Mapped and Unfiled earn none - the first
because nothing is wrong, the second because only a person can decide.

**Move Manifest**
The record of every source-and-destination pair an Action actually moved, filled
in at the moment it is applied. What makes a move into an existing folder
reversible: without it, Atlas cannot tell which items it moved in and which were
already there.

**Stale Plan**
A Plan whose preview no longer describes the drive, because something changed
between the preview and the confirmation. A Stale Plan is never applied - Atlas
abandons it and says what changed.

**Undo Stack**
The Plans applied to one Project during this session, most recent first. Undoing
one applies its inverse, which is itself a Plan and is previewed, confirmed, and
checked for staleness like any other.

**Guard**
What a preview saw, and what has to still be true before Atlas writes. Guard
strength scales with the scope of what it protects: a project-wide conform re-reads
the whole drive and the project root, while a one-Action Plan from a Tree Node
re-reads only the drive map and the directories that Action touches. Both abort
identically - nothing moves, and the operator is told what changed. A guard
deliberately does not see a change it cannot be affected by; that is what makes the
narrow one affordable on a keystroke.

**Path Length Warning**
The longest absolute path an Action would create, measured while the Plan is still
a preview. Atlas warns above 260 characters and never refuses, and never applies
the extended-length prefix on the write side - routing around the limit would let
Atlas create a path Explorer and Revit cannot open, which is the opposite of
warning about it.

## Atlas Project Tree Seam

**Node Key**
A Tree Node's project-relative path, forward-slashed, with `""` for the project
root. The node's stable identity: it survives a refresh, and Atlas can say where a
Node Key went after a write. Necessary because Textual restores the tree cursor by
line number rather than by node identity, so a rebuild with a different child list
would otherwise move the selection silently.

**Project Tree**
The handle core gives the TUI for one Project. Expands lazily - one enumeration per
folder actually displayed - hands out immutable Tree Nodes, and keeps the cache
behind them. It owns filesystem facts; the widget owns interaction.

**Containment**
The rule that decides Filing State below the project root, where the drive map has
no rule of its own. A Tree Node at or under a canonical path is Mapped; one under
an Unfiled node is Unfiled. A path the map names explicitly keeps its own verdict
at any depth.

**Shelf Life**
How long a folder's enumeration may be trusted before Atlas reads it again: 60
seconds. There is no filesystem watching over the Drive redirector, so somebody
else's change reaches the tree when the shelf life expires or when the operator
refreshes, and never sooner.

**Reconcile**
What the tree does after Atlas applies a Plan: forget the folders the Move Manifest
names, take the fresh report with it, and move the cursor to where the repaired
node went. Scoped like the Guard is - a one-node repair forgets two folders, a
project-wide conform forgets the project.
