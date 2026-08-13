# Atlas

Map-driven TUI/CLI for studio shared-drive project tooling. Replaces the PS1/BAT
generation (`New-Project`, `Add-Section`, `Clean-Empty`, `Conform-Project`) per the spec:
`LIBRARY - Reference\_House Standard\atlas-tui-spec.md` (Google Shared Drives).

The drive's `_tools\<drive>-map.json` is the only brain - Atlas hard-codes zero folder names.

## Status: P1 (read-only)

| Command | Does |
|---|---|
| `atlas` | TUI: drive picker + project table with conformance badges |
| `atlas doctor [--drive D] [--json]` | drive-wide read-only conformance report |
| `atlas lint [--drive D] [--json]` | validate the map file itself |

Exit codes: `0` clean, `1` findings/pending work, `2` error. `--json` is the agent interface.

P2 (`new`/`add`/`clean`), P3 (`conform` incl. relocations), P4 (PS1 deprecation) per spec section 11.

## Dev

```bash
cd tools/atlas
uv sync
uv run pytest
uv run atlas doctor --drive "G:/Shared drives/ARCHITECTURE"
```
