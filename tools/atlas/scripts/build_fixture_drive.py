"""Build a throwaway fixture drive that shows all four repairable Filing States.

Never point this at the studio drive. It writes only under the path given.
"""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

FIXTURE_MAP = {
    "drive": "TESTDRIVE",
    "version": "2.0",
    "projectNaming": "YYMMDD_<ShortAddress>-<Description>",
    "controlPlane": {
        "projectFile": "PROJECT.md",
        "decisionsDir": "decisions",
        "handoffsDir": ".agent/handoff",
        "claudeFile": "CLAUDE.md",
        "analysisDir": "06 Research/Code",
    },
    "sections": [
        {"id": "01 Model", "seed": True, "children": ["01 Site Model", "02 Design"]},
        {"id": "06 Research", "seed": True, "children": ["Zoning", "Code"]},
        {"id": "08 OUT", "seed": True, "children": ["Transmittals", "RFI"]},
        {"id": "10 Legal", "seed": False, "children": ["Invoices", "Proposals-Contracts"]},
        {"id": "11 Meetings", "seed": True, "children": ["Agendas", "Minutes"]},
    ],
    "driftMap": {"Meetings": "11 Meetings", "10 Legal Business": "10 Legal"},
    "relocations": {
        "08 OUT/Invoices": "10 Legal/Invoices",
        "HANDOFF-*.md": ".agent/handoff/",
    },
}


def build(root: Path) -> None:
    if root.exists():
        shutil.rmtree(root)
    tools = root / "_tools"
    tools.mkdir(parents=True)
    (tools / "testdrive-map.json").write_text(
        json.dumps(FIXTURE_MAP, indent=2), encoding="utf-8"
    )

    project = root / "260813_120 Bowery-Loft"
    for section in ("01 Model/01 Site Model", "01 Model/02 Design",
                    "06 Research/Zoning", "06 Research/Code",
                    "08 OUT/Transmittals", "08 OUT/RFI",
                    "11 Meetings/Agendas", "11 Meetings/Minutes"):
        (project / section).mkdir(parents=True)

    # Drifted: the map renames "Meetings" to "11 Meetings".
    (project / "Meetings").mkdir()
    (project / "Meetings" / "2026-08-13 kickoff.md").write_text("kickoff", encoding="utf-8")

    # Misplaced: the map relocates "08 OUT/Invoices" to "10 Legal/Invoices".
    (project / "08 OUT" / "Invoices").mkdir()
    (project / "08 OUT" / "Invoices" / "INV-001.pdf").write_text("x", encoding="utf-8")

    # Loose: a file the map sweeps into the handoff dir.
    (project / "HANDOFF-2026-08-13.md").write_text("handoff", encoding="utf-8")

    # Unfiled: nothing in the map accounts for this at all.
    (project / "Random Stuff").mkdir()
    (project / "Random Stuff" / "scratch.txt").write_text("x", encoding="utf-8")

    (project / "PROJECT.md").write_text(
        "# 120 Bowery Loft\n\nFixture project.\n", encoding="utf-8"
    )

    second = root / "260901_44 Pine St"
    (second / "01 Model").mkdir(parents=True)
    (second / "PROJECT.md").write_text("# 44 Pine St\n", encoding="utf-8")

    print(f"built {root}")


if __name__ == "__main__":
    build(Path(sys.argv[1]))
