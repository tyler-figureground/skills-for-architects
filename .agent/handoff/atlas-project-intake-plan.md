# Atlas Project Intake - Implementation Plan

Status: implemented and deployed - production create smoke test intentionally not run
Date: 2026-08-31
Last checkpoint: 2026-08-31 - core, index, CLI, TUI, dossier contract, docs, and 138 tests green
Scope: `tools/atlas`, project-dossier contract, shared ARCHITECTURE drive deployment

## Objective

Replace Atlas's two-field new-project modal with a complete project-intake workflow. Require full project identity, structured site address, project use case, billing contact, and client contact before creation. Reuse a shared contact directory. Generate the short folder name from the site street while writing complete data into `PROJECT.md` and relevant Atlas-generated artifacts.

## Confirmed product decisions

- Shared contacts live per mapped drive at `_tools/billing-contacts.json`.
- Folder format: `YYMMDD_<short address>-<description>`; omit suffix when description is blank.
- Short address: street number + street name/suffix only. Exclude unit, city, state, and ZIP.
- Project Address uses structured US fields: street, optional unit, city, state, ZIP.
- Required project fields: Project Address, Project Name, Project Use Case, Billing Contact, Client Contact.
- Description is optional.
- Project Use Case choices:
  - Renovation
  - Addition
  - Renovation + Addition
  - Ground Up
  - Feasibility
  - Existing Conditions
  - Code Compliance
  - Other
- Other requires a custom use-case label.
- Billing and Client Contact are separate roles.
- Client Contact appears below Billing Contact, defaults to the selected Billing Contact, and can be overridden.
- Both roles use one shared contact directory and the same Add New flow.
- New Contact requires first name, last name, and email. Phone, company, and full mailing address are optional.
- Contact email is unique case-insensitively. Duplicate creation is blocked and the existing contact is selected.
- Every project stores contact stable ID plus a creation-time snapshot.
- TUI uses a three-step wizard: project/address, contacts, final review.
- `atlas new` enforces the same creation contract as the TUI.
- First release populates Atlas-generated files only. No Revit, Word, or spreadsheet template copying.

## Current-state gaps

- `NewProjectModal` collects one overloaded “Project name or address” field and optional descriptor.
- Core `new_project()` accepts primitive name/description strings, so incomplete creation remains possible outside the TUI.
- Folder naming is based on project name, not address.
- `PROJECT.md` leaves address/client blank and has no Project Use Case, billing contact, or client-contact snapshot.
- Atlas has no reusable contact repository.
- CLI `atlas new` cannot express the new required data.
- `_Project Index.md` records only folder, date, descriptor, and status.
- Legacy PowerShell writers and Atlas currently maintain a byte-parity contract that must be deliberately migrated.

## Domain model

Canonical terms live in `/CONTEXT.md`.

### Value objects

`ProjectAddress`
- `street`: required; begins with a street number and includes street name/suffix
- `unit`: optional
- `city`: required
- `state`: required two-letter US postal abbreviation, normalized uppercase
- `postal_code`: required ZIP or ZIP+4
- `formatted`: deterministic one-line full address
- `short`: deterministic street field with unit excluded

`Contact`
- `id`: stable UUID
- `first_name`: required
- `last_name`: required
- `email`: required; trimmed and case-folded for uniqueness
- `phone`: optional; preserve human formatting after basic plausibility validation
- `company`: optional
- `address`: optional structured mailing address
- `created_at`, `updated_at`: UTC timestamps

`ContactSnapshot`
- stable contact ID plus all display fields copied at project creation

`ProjectUseCase`
- closed canonical labels listed above
- `Other` additionally requires `custom_label`
- effective display value is custom label for Other while retaining canonical category `Other`

`ProjectIntake`
- `project_name`
- `project_address`
- `description`
- `project_use_case`
- `billing_contact_snapshot`
- `client_contact_snapshot`
- creation date

### Invariants

- Core creation accepts only a validated `ProjectIntake`; TUI and CLI cannot bypass it.
- Folder name is derived, never entered directly.
- Billing and client snapshots must point to contacts present in the selected drive's directory at validation time.
- Other without a custom label is invalid.
- Description and Project Use Case remain distinct.
- Project Use Case never populates `occupancy_group`.
- Contact mailing address never substitutes for Project Address.

## Architecture and module seams

### 1. Project intake model - new `src/atlas/core/intake.py`

Deep module owning normalization and validation.

Interface:
- immutable dataclasses for `ProjectAddress`, `ProjectUseCase`, `ContactSnapshot`, `ProjectIntake`
- constructors/factories returning normalized valid values or raising `IntakeError`
- `format_full_address(address)`
- `short_address(address)`

Keep regular expressions, state/ZIP validation, YAML-safe formatting, and use-case rules private.

### 2. Contact directory - new `src/atlas/core/contacts.py`

Deep module owning shared-contact persistence.

Interface:
- `load_contacts(drive_root) -> ContactDirectory`
- `add_contact(drive_root, draft) -> Contact`
- `find_contact(directory, id_or_email) -> Contact | None`

Storage schema:

```json
{
  "schemaVersion": 1,
  "contacts": [
    {
      "id": "uuid",
      "firstName": "Ada",
      "lastName": "Lovelace",
      "email": "ada@example.com",
      "phone": "...",
      "company": "...",
      "address": {
        "street": "...",
        "unit": "...",
        "city": "...",
        "state": "NY",
        "postalCode": "11206",
        "country": "US"
      },
      "createdAt": "ISO-8601 UTC",
      "updatedAt": "ISO-8601 UTC"
    }
  ]
}
```

Persistence behavior:
- Missing file means empty directory.
- Reject malformed/unsupported schema with actionable recovery; never silently reset.
- Enforce case-insensitive unique email.
- Write UTF-8 JSON through a sibling temporary file, flush, then atomic replace.
- Use optimistic digest comparison immediately before replace; on concurrent change, reload and retry once. Refuse rather than overwrite unresolved contention.
- Sort display list by last name, first name, company, email.
- Do not log contact personal data.

### 3. Project creation - refactor `src/atlas/core/ops.py`

Change `new_project()` to accept `ProjectIntake` rather than primitive strings.

Creation sequence:
1. Validate complete intake.
2. Reload contact directory and resolve both IDs.
3. Freeze fresh snapshots.
4. Derive and sanitize final folder name from short address + optional description.
5. Refuse existing destination.
6. Create destination exclusively.
7. Seed mapped folders and generated control files.
8. Append expanded project-index row.
9. Write privacy-safe operation log.
10. Return `NewProjectResult` with folder and populated metadata summary.

Preserve constructive-write rules: never overwrite an existing destination or control file. If a later write fails, report exact partial project path and recovery steps; do not delete a folder that a sync client or user may have begun modifying.

### 4. Dossier rendering - refactor `src/atlas/core/projectmd.py`

Render from `ProjectIntake`, not parallel primitive arguments.

Add backward-compatible YAML keys:
- `description`
- `project_use_case`
- `project_use_case_category`
- `billing_contact_id`
- `billing_contact_name`
- `billing_contact_email`
- `billing_contact_phone`
- `billing_contact_company`
- `billing_contact_address`
- `client_contact_id`
- `client_contact_name`
- `client_contact_email`
- `client_contact_phone`
- `client_contact_company`
- `client_contact_address`

Retain existing `project` and `address` keys. Unknown keys remain harmless to Norma and other YAML consumers.

Expand Identity table with:
- Project
- Full Address
- Project Use Case
- Description
- Billing Contact
- Billing Email
- Billing Phone
- Billing Company
- Billing Address
- Client Contact
- Client Email
- Client Phone
- Client Company
- Client Address
- Jurisdiction
- Virtual Tour
- Created
- Drive
- Status

Creation-time provenance should identify `Atlas intake` and creation date where the dossier schema supports source/date. Existing code-table provenance rules remain unchanged.

Escape Markdown table delimiters/newlines in all user values. Quote YAML scalars safely rather than interpolating raw text.

### 5. Project index

Expand new index schema to non-sensitive discovery fields only:
- Project folder
- Project name
- Full project address
- Project use case
- Created
- Description
- Status

Do not place contact email, phone, or mailing address in the drive-wide index.

Migration:
- Detect legacy four-column header.
- Rewrite once to expanded schema while preserving legacy rows and leaving newly unavailable columns blank.
- Write temp + atomic replace.
- Refuse unknown table shapes instead of corrupting hand-edited indexes.
- Add a backup copy under `_tools/logs/` before first schema migration.

### 6. TUI wizard - `src/atlas/tui/app.py`

Replace `NewProjectModal` with a stateful three-step flow.

Step 1 - Project
- Project Name, required
- Street Address, required
- Unit, optional
- City, required
- State selector/input, required
- ZIP, required
- Description, optional
- Project Use Case selector, required
- Custom Use Case, conditionally visible/required for Other
- Live full-address and exact folder-name preview
- Next disabled until valid; show field-specific correction text

Step 2 - Contacts
- Billing Contact selector, required, searchable if Textual permits
- `Add new contact…` action
- Client Contact selector directly below billing
- Client initially mirrors billing; changing billing continues to mirror only until user explicitly overrides client
- Client selector supports the same Add New action
- Nested Add Contact modal with persistent labels and required markers
- Duplicate email error offers/selects existing contact

Step 3 - Review
- Show exact folder path
- Show Project Name, full address, description, effective use case
- Show billing and client contact summaries
- Explain that contact details are snapshotted into `PROJECT.md`
- Back controls preserve entered values
- Create button starts existing background operation pattern
- On stale map/contact data, stop and return user to review with a specific message

Keyboard/accessibility:
- predictable Tab/Shift+Tab order
- Enter advances/submits only when current step is valid
- Escape cancels after confirmation only if entered data would be lost
- visible Back/Next/Create controls
- no required meaning conveyed by color alone

### 7. CLI parity - `src/atlas/cli.py`

Add contact commands:
- `atlas contacts list [--drive] [--json]`
- `atlas contacts add --first-name --last-name --email [--phone] [--company] [structured address flags] [--drive] [--json]`

Refactor `atlas new` required arguments:
- `--name`
- `--street`
- `--city`
- `--state`
- `--zip`
- `--use-case`
- `--billing-contact <id-or-email>`

Optional:
- `--unit`
- `--desc`
- `--other-use-case`
- `--client-contact <id-or-email>`; defaults to billing contact

CLI emits field-specific validation errors and preserves JSON output compatibility by adding fields rather than removing `created`, `path`, and `seeded`.

This is a breaking behavior change for `atlas new`; bump Atlas minor version to `0.2.0` and document migration.

### 8. Project-dossier shared contract

Update:
- `plugins/09-project-dossier/skills/project-dossier/SKILL.md`
- plugin version metadata
- relevant README/CHANGELOG documentation
- `docs/adr/0001-project-md-shared-front-matter-machine-contract.md` cross-reference

Rules:
- Dossier skill recognizes and preserves new intake keys.
- Human Identity rows and front matter stay synchronized.
- Contact snapshots are project facts; later shared-directory edits do not silently rewrite them.
- Updating a project contact requires an explicit dossier update or future Atlas contact-relink flow.
- Project Use Case remains distinct from code occupancy.

Create an ADR for shared contact directory + project snapshot because the choice is durable, cross-file, and trades live updates for historical stability.

### 9. Legacy PowerShell writers and deployment

Atlas README says Atlas replaces PS1/BAT generation, but legacy scripts remain on the drive and currently claim byte parity.

Implementation should:
- make Atlas the canonical path for complete new-project intake;
- update legacy `New-Project.ps1`/`Conform-Project.ps1` dossier templates enough to preserve the expanded blank schema if those scripts remain available;
- clearly mark legacy New Project as unable to create complete intake, or route its BAT launcher to `atlas`;
- remove obsolete “exact byte parity” comments/tests where complete Atlas intake intentionally differs, retaining encoding/line-ending golden tests;
- deploy updated scripts/schema only after repository tests pass and after backing up `_tools` files.

## Validation rules

- Project name: trimmed, non-empty; reject control characters and Markdown-breaking newlines.
- Street: trimmed, begins with a street number; includes additional non-numeric street text.
- City: trimmed, non-empty.
- State: valid two-letter US abbreviation.
- ZIP: `12345` or `12345-6789`.
- Unit: optional; excluded from folder name.
- Description: optional; sanitize existing illegal Windows filename characters.
- Derived folder component: sanitize Windows-illegal characters, collapse whitespace, trim trailing dots/spaces, enforce practical path-length budget, and show final result before creation.
- Use case: canonical list; Other requires non-empty custom label.
- Email: trimmed, basic practical syntax validation, case-insensitive uniqueness.
- Phone: optional; preserve formatting, reject values with no plausible digit count.
- Contact address: optional; when any structured address field is supplied, validate a complete address rather than storing a partial ambiguous value.

## Migration and compatibility

- Existing projects remain valid; no bulk rewrite.
- Doctor may report missing new intake fields as setup findings, not corruption.
- Conform-created stubs include new blank keys/rows but never invent data.
- Existing front-matter readers continue because original keys and semantics remain unchanged.
- Existing contact file absence bootstraps cleanly on first Add New.
- Existing project index migrates safely before first expanded append.
- Preserve UTF-8 without BOM, CRLF, trailing newline for generated project control files.
- Keep editable uv install; source changes become available to global `atlas` immediately.

## Test plan

### Unit - intake and naming
- full US address formatting
- short address excludes unit/city/state/ZIP
- state normalization and invalid state rejection
- ZIP and ZIP+4 validation
- street-number requirement
- every use-case option
- Other custom-label requirement
- Windows filename sanitization
- folder naming with and without description
- YAML quoting and Markdown escaping

### Unit - contacts
- missing store returns empty directory
- first contact creates schema v1 file
- required-field validation
- optional fields round-trip
- email uniqueness ignores case and surrounding whitespace
- malformed/unknown schema fails without modification
- atomic write behavior
- optimistic concurrency conflict refuses overwrite
- stable ordering and lookup by ID/email
- snapshots remain unchanged after directory contact mutation

### Unit/integration - creation
- incomplete `ProjectIntake` cannot reach filesystem writes
- folder derives from address, not Project Name
- all required dossier front-matter keys populated
- all Identity rows populated
- billing/client same-person and different-person cases
- project index expanded row
- privacy-safe logs
- existing destination and concurrent arrival safety
- generated encoding/CRLF/trailing-newline contract
- legacy conform stub remains valid

### TUI pilot tests
- three-step forward/back navigation preserves values
- required-field gating and visible errors
- Other reveals required custom input
- live folder preview
- contact list loads from selected drive
- Add New saves and selects contact
- duplicate email selects existing without duplicate write
- client initially mirrors billing
- manual client override persists when billing changes
- review displays exact data
- final creation writes expected folder/dossier
- stale contact/map state blocks creation safely
- cancel behavior and keyboard flow

### CLI tests
- all required flags enforced
- contact add/list human and JSON modes
- lookup by ID and email
- client defaults to billing
- Other requires custom label
- TUI and CLI produce equivalent `ProjectIntake` and dossier output
- JSON output remains additive

### Contract/regression
- Norma can still parse populated `PROJECT.md`
- project-dossier skill/template contains every new key/row
- repository lint passes
- full `uv run pytest` passes
- live TUI smoke test against a disposable fixture drive, never production drive

## Delivery phases

### Phase 1 - contracts and tests - COMPLETE
- Added validated domain/value objects and red-green tests.
- Added contact schema/repository with persistence, duplicate-contact result, writer lock, atomic replacement, and contention tests.
- Recorded ADR 0003.

Exit evidence: `uv run pytest tests/test_intake.py tests/test_contacts.py -q` - 32 passed.

### Phase 2 - creation and dossier - COMPLETE
- Refactored `new_project()` around contact references resolved to fresh snapshots.
- Expanded dossier rendering and shared conform-stub schema.
- Added safe expanded project-index creation/migration with backups.
- Updated all core call sites and tests.

Exit evidence: fixture-drive creation produces complete dossier and safe index.

### Phase 3 - CLI - COMPLETE
- Added contact list/add subcommands and complete `atlas new` flags.
- Added 18 CLI integration and JSON contract tests.

Exit evidence: complete headless creation works from any directory.

### Phase 4 - TUI - COMPLETE
- Built three-step wizard and nested Add Contact flow.
- Added validation, exact preview, map/contact stale-data protection, default Client Contact behavior, and pilot tests.

Exit evidence: complete intake and Add New Contact flows pass fixture-drive pilot tests.

### Phase 5 - shared contract and release metadata - COMPLETE
- Updated dossier skill, plugin metadata, README, changelog, ADR cross-references, and Atlas version 0.2.0.
- Preserved additive Norma contract compatibility.
- Production drive map and legacy script deployment moved to Phase 6 because they mutate shared production state.

Exit evidence: full Atlas suite and repo lint green.

### Phase 6 - production deployment and verification - COMPLETE WITH NON-DESTRUCTIVE SCOPE
- Backed up map, launchers, and drive instructions under `_tools/logs/atlas-0.2.0-deploy-20260902-134754/`.
- Deployed and pinned `studio_atlas-0.2.0-py3-none-any.whl`.
- Redirected legacy `New-Project.bat` to Atlas.
- Updated project naming declaration and drive instructions.
- Verified deployed launcher reports Atlas 0.2.0 and production map parses/lints.
- Did not add a contact or create/delete a production test project, matching approved deployment scope.

Exit evidence: deployed launcher `atlas 0.2.0`; production lint completed with two pre-existing duplicate-child warnings and no errors.

## Acceptance criteria

1. User cannot create a project without Project Name, complete Project Address, Project Use Case, Billing Contact, and Client Contact.
2. Other requires a custom use-case label.
3. Folder preview and created folder equal `YYMMDD_<street number + street>-<description>`.
4. Full address and all project/contact facts appear in `PROJECT.md`.
5. Billing and client default to the same contact but can differ.
6. Add New Contact persists to the shared drive and is immediately selectable.
7. Duplicate email never creates a second contact.
8. Project snapshots remain unchanged when shared contact data later changes.
9. TUI and CLI enforce the same core invariants.
10. Existing projects and Norma parsing remain functional.
11. No contact personal data enters Atlas logs or drive-wide project index.
12. Full tests, repo lint, and fixture-drive live TUI verification pass before release.

## Explicitly deferred

- Editing/deleting/merging contacts from Atlas.
- External CRM/accounting/Google Contacts synchronization.
- International project-address formats.
- Address autocomplete or deliverability verification.
- Revit/Word/Excel template copying and field injection.
- Automatic refresh of historical project snapshots after contact edits.
- Bulk migration of existing projects into the new intake schema.

## Risks and mitigations

- Shared-drive concurrent contact writes: optimistic digest + atomic replace + refuse unresolved conflicts.
- PII spread: full snapshots only in per-project dossier; index/log omit contact details.
- YAML/Markdown injection: centralized serializers and escaping tests.
- Folder ambiguity: structured address and exact review preview.
- Contract drift: update Atlas renderer, dossier skill, ADR, and parity tests in one release.
- Legacy creation bypass: require CLI parity and redirect/deprecate old New-Project launcher.
- Partial filesystem creation: validate first, exclusive writes, precise partial-state reporting, never unsafe cleanup.
