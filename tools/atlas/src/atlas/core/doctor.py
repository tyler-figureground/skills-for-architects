"""Build the read-only conformance report: `atlas doctor`.

Pure over scan facts wherever possible; the only extra I/O is existence and
file-count probes on relocation sources (small by construction). P1 is strictly
read-only - the fix flags (--fix-index, --fix-project-md) land in later phases.
"""

from __future__ import annotations

import fnmatch
import os
from dataclasses import dataclass, field
from pathlib import Path

from .mapfile import DriveMap
from .scan import DriveInventory, ProjectInventory, count_files

# Files tolerated at a project root without being flagged: OS noise plus the
# PRD-209 time-ledger family, which is blessed control plane per the map note.
TOLERATED_ROOT_FILES = ("desktop.ini", "jdp-time-ledger.ndjson", "jdp-time-ledger.ndjson.*")

STATUS_CONFORM = "conform"
STATUS_DRIFT = "drift"
STATUS_UNFILED = "unfiled"
STATUS_STUB = "stub"


@dataclass(frozen=True)
class RelocationHit:
    source: str
    target: str
    file_count: int


@dataclass(frozen=True)
class ProjectReport:
    name: str
    status: str
    sections_present: int
    missing_control_plane: tuple[str, ...] = ()
    drift: tuple[tuple[str, str], ...] = ()          # (found-name, canonical)
    relocations: tuple[RelocationHit, ...] = ()
    sweeps: tuple[tuple[str, str], ...] = ()          # (root file, target dir)
    unfiled: tuple[str, ...] = ()

    @property
    def actionable(self) -> bool:
        return bool(self.missing_control_plane or self.drift or self.relocations or self.sweeps)


@dataclass(frozen=True)
class DriveReport:
    root: Path
    drive: str
    map_version: str
    projects: tuple[ProjectReport, ...]

    def summary(self) -> dict[str, int]:
        counts = {STATUS_CONFORM: 0, STATUS_DRIFT: 0, STATUS_UNFILED: 0, STATUS_STUB: 0}
        for p in self.projects:
            counts[p.status] += 1
        return counts


def _control_plane_paths(m: DriveMap) -> dict[str, str]:
    paths = {
        m.project_file: m.project_file,
        m.decisions_dir: m.decisions_dir,
        m.claude_file: m.claude_file,
    }
    if m.analysis_dir:
        paths[m.analysis_dir] = m.analysis_dir
    return paths


def _tolerated(name: str) -> bool:
    return any(fnmatch.fnmatch(name.lower(), pat.lower()) for pat in TOLERATED_ROOT_FILES)


def _dir_exists_exact(base: Path, rel: str) -> bool:
    """Directory existence with exact-case name matching.

    Path.is_dir() is case-insensitive on the Windows/Google Drive mount, so a
    relocation whose source and target differ only by case ("change Orders" ->
    "Change Orders") false-positives forever after the rename. Walk each
    segment and require the exact on-disk name.
    """
    current = base
    for segment in rel.replace("\\", "/").split("/"):
        try:
            with os.scandir(current) as it:
                match = next(
                    (e for e in it if e.name == segment and e.is_dir(follow_symlinks=False)),
                    None,
                )
        except OSError:
            return False
        if match is None:
            return False
        current = current / segment
    return True


def report_project(inv: ProjectInventory, m: DriveMap) -> ProjectReport:
    section_ids = set(m.section_ids)
    drift_lower = {k.lower(): v for k, v in m.drift_map.items()}
    root_names = {e.name for e in inv.root_entries}

    sections_present = sum(1 for e in inv.root_entries if e.is_dir and e.name in section_ids)

    # Control plane: report what Conform would backfill.
    missing: list[str] = []
    for label in (m.project_file, m.decisions_dir, m.claude_file):
        if label and label not in root_names:
            missing.append(label)
    if m.analysis_dir and not (inv.path / m.analysis_dir).exists():
        missing.append(m.analysis_dir)

    # driftMap: top-level dirs whose (case-insensitive) name is a known drift.
    drift: list[tuple[str, str]] = []
    for e in inv.root_entries:
        if e.is_dir and e.name not in section_ids and e.name.lower() in drift_lower:
            drift.append((e.name, drift_lower[e.name.lower()]))

    # relocations: dir sources that exist, glob sources matched at root.
    reloc_hits: list[RelocationHit] = []
    sweeps: list[tuple[str, str]] = []
    for src, dst in m.relocations.items():
        if "*" in src or "?" in src:
            for e in inv.root_entries:
                if not e.is_dir and fnmatch.fnmatch(e.name, src):
                    sweeps.append((e.name, dst))
            continue
        if _dir_exists_exact(inv.path, src):
            src_path = inv.path / src
            reloc_hits.append(RelocationHit(source=src, target=dst, file_count=count_files(src_path)))

    # Unfiled: whatever the canon, control plane, pending actions, and
    # tolerated set do not explain.
    explained = set(section_ids)
    explained.update(p.split("/")[0].split("\\")[0] for p in _control_plane_paths(m))
    if m.handoffs_dir:
        explained.add(m.handoffs_dir.replace("\\", "/").split("/")[0])
    explained.update(name for name, _ in drift)
    explained.update(h.source for h in reloc_hits)
    swept = {name for name, _ in sweeps}
    unfiled = sorted(
        e.name
        for e in inv.root_entries
        if e.name not in explained and e.name not in swept and not _tolerated(e.name)
    )

    if sections_present == 0:
        status = STATUS_STUB
    elif missing or drift or reloc_hits or sweeps:
        status = STATUS_DRIFT
    elif unfiled:
        status = STATUS_UNFILED
    else:
        status = STATUS_CONFORM

    return ProjectReport(
        name=inv.name,
        status=status,
        sections_present=sections_present,
        missing_control_plane=tuple(missing),
        drift=tuple(drift),
        relocations=tuple(reloc_hits),
        sweeps=tuple(sweeps),
        unfiled=tuple(unfiled),
    )


def report_drive(inventory: DriveInventory) -> DriveReport:
    return DriveReport(
        root=inventory.root,
        drive=inventory.map.drive,
        map_version=inventory.map.version,
        projects=tuple(report_project(p, inventory.map) for p in inventory.projects),
    )


def report_to_dict(report: DriveReport) -> dict:
    return {
        "drive": report.drive,
        "root": str(report.root),
        "map_version": report.map_version,
        "summary": report.summary(),
        "projects": [
            {
                "name": p.name,
                "status": p.status,
                "sections_present": p.sections_present,
                "missing_control_plane": list(p.missing_control_plane),
                "drift": [{"from": a, "to": b} for a, b in p.drift],
                "relocations": [
                    {"source": h.source, "target": h.target, "files": h.file_count}
                    for h in p.relocations
                ],
                "sweeps": [{"file": a, "target": b} for a, b in p.sweeps],
                "unfiled": list(p.unfiled),
            }
            for p in report.projects
        ],
    }
