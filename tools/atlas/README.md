# Atlas

Map-driven TUI/CLI for studio shared-drive project tooling. Replaces the PS1/BAT
generation (`New-Project`, `Add-Section`, `Clean-Empty`, `Conform-Project`) per the spec:
`LIBRARY - Reference\_House Standard\atlas-tui-spec.md` (Google Shared Drives).

The drive's `_tools\<drive>-map.json` is the only folder-structure brain - Atlas hard-codes zero canonical folder names. Reusable contacts live beside it in `_tools\billing-contacts.json`.

## Status: operations console

Atlas diagnoses and safely repairs mapped project-folder differences. Every mutation uses the
same core plan as the CLI. Conform previews exact changes, never overwrites destinations, and
leaves conflicts in place. Clean removes file-empty folders only.

| Command | Does |
|---|---|
| `atlas` | Interactive operations console: inspect, filter, sort, create, clean, and conform |
| `atlas doctor [--drive D] [--json]` | Drive-wide read-only conformance report |
| `atlas lint [--drive D] [--json]` | Validate the map file itself |
| `atlas new --name NAME --street STREET --city CITY --state ST --zip ZIP --use-case USE_CASE --billing-contact ID_OR_EMAIL [...]` | Create a complete mapped project |
| `atlas contacts list [--drive D] [--json]` | List reusable drive contacts |
| `atlas contacts add --first-name FIRST --last-name LAST --email EMAIL [...]` | Add a reusable drive contact |
| `atlas contacts edit ID_OR_EMAIL [--yes] [...]` | Edit a shared contact; stable ID retained |
| `atlas project edit FOLDER [--yes] [...]` | Edit project intake; safely preview/confirm folder rename |
| `atlas add --project NAME --section SECTION` | Add map-approved project folders |
| `atlas clean --project NAME [--apply]` | Preview or remove empty folders |
| `atlas conform --project NAME [--apply]` | Preview or apply mapped repairs |

TUI keys: `n` new project, `e` edit selected project, `m` manage contacts, `/` filter,
`Enter` inspect, `Space` mark, `x` conform marked, `a` add folders, `f` conform, `?` help,
`Ctrl+P` command palette. Additional actions remain searchable in the palette.

Exit codes: `0` clean, `1` findings/pending work, `2` error. `--json` is the agent interface.

## New project intake

Press `n` in the TUI. Three steps collect:

1. Required Project Name, structured US Project Address, and Project Use Case; optional Description
2. Required Billing Contact and Client Contact; Client defaults to Billing but can be overridden
3. Exact folder, project facts, and contact review before creation

Folder format: `YYMMDD_<street number + street>-<description>`. Unit, city, state, and ZIP remain in `PROJECT.md` but stay out of the folder name. Selecting **Other** as Project Use Case requires a custom label. **Add new contact…** writes to the selected drive's shared contact directory; first name, last name, and email are required.

## Editing projects and contacts

Select a project and press `e`. Atlas pre-populates every intake field, shows the derived folder name, then requires a second confirmation when Address or Description changes the folder path. It refuses collisions and updates `PROJECT.md` plus the project-index row together. Project contact reassignment refreshes that project's snapshots only.

Press `m` to edit the shared contact directory. Contact IDs remain stable. Contact mailing addresses accept numbered streets, `PO Box`, and `P.O. Box`; project site addresses still require a physical numbered street. Shared contact edits do not rewrite historical project snapshots.

CLI edit commands are interactive when run in a terminal. Omitted fields retain their current values. Automation and `--json` require `--yes`; a folder rename also requires separate `--rename` approval. Use `--dry-run` to inspect the project-update plan without changing files. Run `atlas project edit --help` or `atlas contacts edit --help` for field flags.

## Accessibility

Atlas has not been validated with assistive technology and makes no accessibility conformance claim. Textual's screen-reader support is unresolved upstream ([textual#2425](https://github.com/Textualize/textual/issues/2425)), so the console should not be assumed usable with a screen reader.

Every capability that writes, and every fact the console can show, is also reachable from the CLI with `--json`. That path is plain text and is the supported one for automation - and for anyone the console does not serve.

Within the console, colour reinforces a distinction and never carries one alone. A folder or file with something wrong with it names what is wrong in words; when the terminal is too narrow for the full phrase the word abbreviates - `NAME`, `PLACE`, `LOOSE`, `UNMAPPED` - rather than leaving the glyph and its colour to say it.

## Install

Install once as an editable uv tool. The `atlas` command then works from any directory, and local source changes take effect without reinstalling.

```bash
cd tools/atlas
uv tool install --editable .
atlas
```

If `atlas` is not found after installation, add uv's tool directory to `PATH`:

```bash
uv tool update-shell
```

## Dev

```bash
cd tools/atlas
uv sync
uv run pytest
atlas doctor --drive "G:/Shared drives/ARCHITECTURE"
```
