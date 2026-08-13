"""Fixture drive builder: a miniature mapped drive in tmp_path."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

FIXTURE_MAP = {
    "drive": "TESTDRIVE",
    "version": "2.0",
    "projectNaming": "YYMMDD_<Name>-<Descriptor>",
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
        "_note": "commentary keys are ignored",
        "08 OUT/Invoices": "10 Legal/Invoices",
        "HANDOFF-*.md": ".agent/handoff/",
    },
}


def write_map(drive: Path, data: dict | None = None) -> Path:
    tools = drive / "_tools"
    tools.mkdir(parents=True, exist_ok=True)
    map_path = tools / "testdrive-map.json"
    map_path.write_text(json.dumps(data or FIXTURE_MAP), encoding="utf-8")
    return map_path


def make_project(drive: Path, name: str, *, sections: list[str] = (), files: dict[str, str] | None = None) -> Path:
    project = drive / name
    project.mkdir(parents=True, exist_ok=True)
    for section in sections:
        (project / section).mkdir(parents=True, exist_ok=True)
    for rel, content in (files or {}).items():
        target = project / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
    return project


@pytest.fixture()
def fixture_drive(tmp_path: Path) -> Path:
    drive = tmp_path / "TESTDRIVE"
    drive.mkdir()
    write_map(drive)
    return drive
