# Shared contact directory with project snapshots

Atlas stores reusable contacts once per mapped drive in `_tools/billing-contacts.json`. A project records both each selected contact's stable directory ID and a complete creation-time snapshot in `PROJECT.md`. The directory avoids repeated entry across projects; the snapshot keeps billing and client facts historically stable when a shared contact later changes.

## Consequences

Contact email is unique case-insensitively within a drive. Billing Contact and Client Contact use the same directory but remain separate project roles. Shared-contact edits do not silently rewrite existing projects; changing a project's recorded contact requires an explicit dossier update or future relink operation. Contact personal data stays out of the drive-wide project index and Atlas logs.
