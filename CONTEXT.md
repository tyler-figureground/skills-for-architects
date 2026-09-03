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
A folder Tree Node whose Load State is Read and which has no children. Only a Read
folder can be known to be empty.

