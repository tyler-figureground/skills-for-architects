# Atlas

Map-driven TUI/CLI for studio shared-drive project tooling. Replaces the PS1/BAT
generation (`New-Project`, `Add-Section`, `Clean-Empty`, `Conform-Project`) per the spec:
`LIBRARY - Reference\_House Standard\atlas-tui-spec.md` (Google Shared Drives).

The drive's `_tools\<drive>-map.json` is the only brain - Atlas hard-codes zero folder names.

## Status: operations console

Atlas diagnoses and safely repairs mapped project-folder differences. Every mutation uses the
same core plan as the CLI. Conform previews exact changes, never overwrites destinations, and
leaves conflicts in place. Clean removes file-empty folders only.

| Command | Does |
|---|---|
| `atlas` | Interactive operations console: inspect, filter, sort, create, clean, and conform |
| `atlas doctor [--drive D] [--json]` | Drive-wide read-only conformance report |
| `atlas lint [--drive D] [--json]` | Validate the map file itself |
| `atlas new --name NAME [--desc DESC]` | Create a mapped project |
| `atlas add --project NAME --section SECTION` | Add map-approved project folders |
| `atlas clean --project NAME [--apply]` | Preview or remove empty folders |
| `atlas conform --project NAME [--apply]` | Preview or apply mapped repairs |

TUI keys: `/` filter, `Enter` inspect, `Space` mark, `x` conform marked,
`a` add folders, `f` conform, `?` help, `Ctrl+P` command palette. Additional
actions remain searchable in the palette.

Exit codes: `0` clean, `1` findings/pending work, `2` error. `--json` is the agent interface.

## Dev

```bash
cd tools/atlas
uv sync
uv run pytest
uv run atlas doctor --drive "G:/Shared drives/ARCHITECTURE"
```
