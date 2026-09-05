"""Drive the repair flow with keys only, and show the drive after each step."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

from atlas.tui.app import AtlasApp

STEPS = [
    ("drill into the tree", ["enter"]),
    ("cursor down to the drifted folder", ["down"] * 4),
    ("arm the repair", ["f"]),
    ("confirm", ["enter"]),
    ("undo", ["u"]),
]


def op_line(app) -> str:
    from textual.widgets import Static
    return str(app.query_one("#operation", Static).content)


def tree_rows(app) -> list[str]:
    out = []
    for strip_ in app.screen._compositor.render_strips():
        line = "".join(seg.text for seg in strip_).rstrip()
        if "█" in line or "▚" in line:
            out.append(line.strip())
    return out


async def main() -> None:
    drive = Path(sys.argv[1])
    width = int(sys.argv[2]) if len(sys.argv) > 2 else 87
    app = AtlasApp(drive, follow_debounce=0)
    async with app.run_test(size=(width, 51)) as pilot:
        for _ in range(3):
            await app.workers.wait_for_complete()
            await pilot.pause()
        for label, keys in STEPS:
            for key in keys:
                await pilot.press(key)
                for _ in range(3):
                    await app.workers.wait_for_complete()
                    await pilot.pause()
            print(f"--- {label} ({' '.join(keys)}) at {width} cols")
            print(f"    operation: {op_line(app)}")
            for row in tree_rows(app):
                print(f"    {row}")
            print()


asyncio.run(main())
