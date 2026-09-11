# Atlas Project and Contact Editing Plan

Status: complete; production deployed and requested typo corrected
Date: 2026-09-02

## Objective

Add safe editing for existing project intake fields and shared contacts from Atlas TUI and CLI. Project edits may rename the project folder after explicit preview/confirmation. Contact mailing addresses accept physical street addresses or PO boxes; Project Address remains a physical street address.

## Confirmed decisions

- Select project + `e`: Edit project.
- `m`: Manage contacts.
- Both actions appear in `Ctrl+P` command palette.
- CLI parity: `atlas project edit` and `atlas contacts edit`.
- Edit project covers Project Name, full Project Address, Description, Project Use Case, Billing Contact assignment, Client Contact assignment.
- Project contact changes refresh that project's snapshots but do not mutate shared contacts.
- Contact Manager separately edits shared first/last name, email, phone, company, and mailing address.
- Address/Description changes preview old folder → new folder and require explicit rename confirmation.
- Rename refuses an existing destination.
- Contact mailing address accepts `PO Box`, `P.O. Box`, or physical street. City/state/ZIP remain required when any mailing-address field is supplied.
- Project Address continues requiring street number + physical street.

## Public seams

1. `core.contacts`
   - `MailingAddress`
   - `update_contact(drive_root, contact_id, draft) -> Contact`
   - existing add/load/find interfaces remain compatible

2. `core.project_data`
   - `load_project_record(project_path) -> ProjectRecord`
   - `preview_project_update(drive_root, project_path, intake) -> ProjectUpdatePlan`
   - `apply_project_update(drive_root, drive_map, plan) -> ProjectUpdateResult`
   - preserves non-intake dossier content and rejects stale source state

3. `core.project_index`
   - update one existing row by old folder name; never append a duplicate

4. TUI
   - existing intake wizard supports pre-populated edit mode
   - explicit rename confirmation
   - Contact Manager list/edit form

5. CLI
   - project and contact edit commands cross the same core seams

## Safety invariants

- Never overwrite an existing project-folder destination.
- Never rewrite malformed/legacy dossier intake data silently.
- Preserve all dossier content outside known front-matter keys and Identity rows.
- Update front matter and Identity mirror together.
- Stable contact ID survives shared contact edits.
- Case-insensitive email uniqueness excludes the contact being edited.
- Project snapshots change only through explicit project edit.
- Project-index row changes in place; contact PII remains excluded.
- Stale dossier/contact/index state stops before overwrite with actionable recovery.

## Verification

- 201 Atlas tests pass, including PO boxes, case-only renames, rollback, stale writes, legacy index migration, trailing index prose, TUI edit/contact flows, and CLI gates.
- TUI pilots verify `e` pre-population, typo correction, explicit rename confirmation, `m` contact editing, duplicate-email guidance, and PO-box acceptance.
- CLI tests verify interactive, JSON, `--yes`, separate `--rename`, and non-mutating `--dry-run` modes.
- Repository `scripts/lint.sh` passes; shellcheck unavailable locally and skipped by the lint script.
- `git diff --check` passes.
- Built `dist/studio_atlas-0.3.0-py3-none-any.whl`; global editable command reports `atlas 0.3.0` outside the repo.
- Independent re-review confirmed all original blockers fixed. Follow-up findings around dry-run index mutation, trailing index prose, conform rows, and duplicate-email guidance were also fixed.
- User approved production deployment and exact `GROOVE` → `GROVE` correction.

## Production deployment

- Backup: `G:/Shared drives/ARCHITECTURE/_tools/logs/atlas-0.3.0-deploy-20260902-164056/`.
- Final post-review wheel deployed: `G:/Shared drives/ARCHITECTURE/_tools/atlas/studio_atlas-0.3.0-py3-none-any.whl` (SHA-256 `6414fb028f28aec94509c3a1790426be503c4f7a709269e66eb1fb129c8436b0`).
- `Atlas.bat` pinned to 0.3.0; deployed launcher reports `atlas 0.3.0`.
- `HOW-TO.md` documents `e` project editing and `m` contact management.
- Approved dry run previewed a live project folder with a misspelled street name being
  renamed to the corrected spelling (name redacted: real client project).
- Approved apply renamed the folder and changed Project Address to the corrected address.
- Verified old folder absent, new folder present, dossier formatted/structured/Identity address values agree, and project index has exactly one new-folder row and zero old-folder rows.
- Production map lint reports only pre-existing `DUP-CHILD` warnings for `Photos` and `Sketches`.
