"""Load and validate <drive>-map.json (schema v2).

The map is the only brain: Atlas hard-codes zero folder names. See the spec's
schema table (atlas-tui-spec.md section 8) for the contract this module reads.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path


class MapError(Exception):
    """The map file is missing, unparseable, or structurally invalid."""


@dataclass(frozen=True)
class Section:
    id: str
    seed: bool = False
    children: tuple[str, ...] = ()


@dataclass(frozen=True)
class DriveMap:
    path: Path
    drive: str
    version: str
    project_naming: str
    sections: tuple[Section, ...]
    drift_map: dict[str, str] = field(default_factory=dict)
    relocations: dict[str, str] = field(default_factory=dict)
    control_plane: dict[str, str] = field(default_factory=dict)

    @property
    def section_ids(self) -> tuple[str, ...]:
        return tuple(s.id for s in self.sections)

    def section(self, section_id: str) -> Section | None:
        for s in self.sections:
            if s.id == section_id:
                return s
        return None

    # Control-plane accessors with the same defaults the PS1 tools use, so a
    # sparse map behaves identically across tool generations.
    @property
    def project_file(self) -> str:
        return self.control_plane.get("projectFile", "PROJECT.md")

    @property
    def decisions_dir(self) -> str:
        return self.control_plane.get("decisionsDir", "decisions")

    @property
    def claude_file(self) -> str:
        return self.control_plane.get("claudeFile", "CLAUDE.md")

    @property
    def analysis_dir(self) -> str:
        return self.control_plane.get("analysisDir", "")

    @property
    def handoffs_dir(self) -> str:
        return self.control_plane.get("handoffsDir", "")


def find_map(drive_root: Path) -> Path | None:
    """Locate the drive's map: _tools/*-map.json, ignoring _deprecated."""
    tools = drive_root / "_tools"
    if not tools.is_dir():
        return None
    candidates = sorted(
        p for p in tools.glob("*-map.json") if p.parent.name != "_deprecated"
    )
    return candidates[0] if candidates else None


def load_map(path: Path) -> DriveMap:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except OSError as e:
        raise MapError(f"cannot read map: {path}: {e}") from e
    except json.JSONDecodeError as e:
        raise MapError(f"map is not valid JSON: {path}: {e}") from e

    for key in ("drive", "version", "sections"):
        if key not in raw:
            raise MapError(f"map missing required key '{key}': {path}")

    sections: list[Section] = []
    for entry in raw["sections"]:
        if "id" not in entry:
            raise MapError(f"section without 'id' in {path}")
        sections.append(
            Section(
                id=entry["id"],
                seed=bool(entry.get("seed", False)),
                children=tuple(entry.get("children", ())),
            )
        )

    # Keys beginning with "_" inside relocations are commentary, not rules.
    relocations = {
        k: v for k, v in raw.get("relocations", {}).items() if not k.startswith("_")
    }

    return DriveMap(
        path=path,
        drive=raw["drive"],
        version=str(raw["version"]),
        project_naming=raw.get("projectNaming", ""),
        sections=tuple(sections),
        drift_map=dict(raw.get("driftMap", {})),
        relocations=relocations,
        control_plane=dict(raw.get("controlPlane", {})),
    )
