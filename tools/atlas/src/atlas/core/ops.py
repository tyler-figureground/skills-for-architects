"""P2 mutating operations: new project, add section, clean empty.

Safety posture (spec section 6): `new` and `add` are purely constructive and
refuse to touch anything that exists; `clean` is the destructive one and is
dry-run by default with rmdir-only semantics (a directory containing any file
is never deletable). Every applied mutation appends to the drive log.

The full Plan/apply formalism arrives with P3 conform, where plans get long
and reviewable; these three flows have at most a handful of deterministic
steps each.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path

from .mapfile import DriveMap
from .naming import build_folder_name, clean_name_part
from .projectmd import (
    claude_md_lines,
    decisions_readme_lines,
    project_md_lines,
    write_crlf_no_bom,
)


class OpsError(Exception):
    """A requested operation is invalid (exists already, unblessed name, ...)."""


def append_log(drive_root: Path, message: str) -> None:
    log_dir = drive_root / "_tools" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / f"atlas-{datetime.now():%Y%m%d}.log"
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with log_path.open("a", encoding="utf-8", newline="\n") as fh:
        fh.write(f"{stamp} {message}\n")


# ---------------------------------------------------------------- new project

@dataclass(frozen=True)
class NewProjectResult:
    path: Path
    folder_name: str
    seeded: tuple[str, ...]


def new_project(drive_root: Path, m: DriveMap, raw_name: str, raw_desc: str = "", created: date | None = None) -> NewProjectResult:
    name = clean_name_part(raw_name)
    desc = clean_name_part(raw_desc)
    if not name:
        raise OpsError("a project name is required")
    created = created or date.today()
    folder_name = build_folder_name(created, name, desc)
    project = drive_root / folder_name
    if project.exists():
        raise OpsError(f"a folder named '{folder_name}' already exists")

    project.mkdir()
    seeded = []
    for section in m.sections:
        if not section.seed:
            continue
        (project / section.id).mkdir()
        seeded.append(section.id)

    write_crlf_no_bom(project / m.project_file, project_md_lines(m, folder_name, name, desc, created))
    decisions = project / m.decisions_dir
    decisions.mkdir()
    write_crlf_no_bom(decisions / "README.md", decisions_readme_lines())
    if m.analysis_dir:
        (project / m.analysis_dir).mkdir(parents=True, exist_ok=True)
    write_crlf_no_bom(project / m.claude_file, claude_md_lines(m))

    _append_index_row(drive_root, m, folder_name, desc, created)
    append_log(drive_root, f"[{folder_name}] new: seeded {', '.join(seeded)}; control plane written")
    return NewProjectResult(path=project, folder_name=folder_name, seeded=tuple(seeded))


def _append_index_row(drive_root: Path, m: DriveMap, folder_name: str, desc: str, created: date) -> None:
    index = drive_root / "_Project Index.md"
    if not index.exists():
        write_crlf_no_bom(index, [
            f"# {m.drive} - Project Index",
            "",
            "Auto-maintained by New-Project. One row per project (searchable table of contents).",
            "",
            "| Project folder | Created | Descriptor | Status |",
            "|---|---|---|---|",
        ])
    with index.open("a", encoding="utf-8", newline="") as fh:
        fh.write(f"| {folder_name} | {created.strftime('%Y-%m-%d')} | {desc} | Active |\r\n")


# ---------------------------------------------------------------- add section

def add_sections(drive_root: Path, m: DriveMap, project: Path, requests: list[str]) -> list[str]:
    """Create blessed folders. Requests are 'NN Section' or 'NN Section/Child'
    where Child must be a blessed child entry (children may themselves contain
    slashes, e.g. '00 Library/Families'). No free-text names, ever."""
    created: list[str] = []
    for req in requests:
        rel = _resolve_blessed(m, req)
        target = project / rel
        if target.exists():
            continue
        target.mkdir(parents=True)
        created.append(rel)
    if created:
        append_log(drive_root, f"[{project.name}] add: {', '.join(created)}")
    return created


def _resolve_blessed(m: DriveMap, request: str) -> str:
    req = request.replace("\\", "/").strip().strip("/")
    for section in m.sections:
        if req == section.id:
            return section.id
        prefix = section.id + "/"
        if req.startswith(prefix):
            child = req[len(prefix):]
            if child in section.children:
                return f"{section.id}/{child}"
            raise OpsError(f"'{child}' is not a blessed child of '{section.id}'")
    raise OpsError(f"'{request}' is not a canonical section (check the map)")


# ---------------------------------------------------------------- clean empty

def find_empty_dirs(project: Path, m: DriveMap, include_seeds: bool = False) -> list[str]:
    """Directories removable by pure rmdir cascade: no file anywhere beneath.
    Control-plane dirs are always kept; seed section tops kept unless asked."""
    protected_tops = {m.decisions_dir}
    if m.handoffs_dir:
        protected_tops.add(m.handoffs_dir.replace("\\", "/").split("/")[0])
    # The analysisDir is control plane: doctor reports it missing, so clean
    # must never be the thing that removes it.
    analysis_rel = m.analysis_dir.replace("\\", "/") if m.analysis_dir else None
    seed_ids = {s.id for s in m.sections if s.seed}

    empties: list[str] = []
    for root, dirs, files in os.walk(project, topdown=False, followlinks=False):
        root_path = Path(root)
        if root_path == project:
            continue
        rel = root_path.relative_to(project).as_posix()
        top = rel.split("/")[0]
        if top in protected_tops:
            continue
        if analysis_rel and rel == analysis_rel:
            continue
        if not include_seeds and rel in seed_ids:
            continue
        # Empty means: no files here, and every subdir already marked empty.
        if files:
            continue
        if all(f"{rel}/{d}" in empties for d in dirs):
            empties.append(rel)
    return sorted(empties)


def remove_empty_dirs(drive_root: Path, project: Path, rels: list[str]) -> list[str]:
    """rmdir deepest-first; refuses (skips) anything non-empty by construction."""
    removed: list[str] = []
    for rel in sorted(rels, key=lambda r: r.count("/"), reverse=True):
        target = project / rel
        try:
            target.rmdir()
            removed.append(rel)
        except OSError:
            pass  # gained content since the scan; rmdir-only means we skip
    if removed:
        append_log(drive_root, f"[{project.name}] clean: removed {len(removed)} empty dirs")
    return removed
