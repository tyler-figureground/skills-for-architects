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
