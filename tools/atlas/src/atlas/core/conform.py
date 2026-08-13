"""P3: conform a project to the map - plan, then apply.

The plan is derived from doctor's ProjectReport (one fact-gathering pass, one
brain). Apply executes in fixed order: control-plane backfill, driftMap
renames, relocations, sweeps. Safety rules are the spec's section 6, verbatim:
deletions are rmdir-shaped (file-empty only), moves never clobber (collisions
survive in place and are reported), case-only renames go through a temp name,
every applied action is logged.

Control-plane backfill keeps parity with Conform-Project.ps1: an existing
PROJECT.md that lacks the YAML machine contract gets it PREPENDED with the
prose preserved; nothing existing is ever overwritten.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, replace
from pathlib import Path

from .doctor import ProjectReport
from .mapfile import DriveMap
from .ops import append_log
from .projectmd import (
    FRONT_MATTER_HEAD,
    FRONT_MATTER_KEYS,
    claude_md_lines,
    decisions_readme_lines,
    write_crlf_no_bom,
)

# Action kinds, in apply order.
BACKFILL = "backfill"
RENAME = "rename"
RELOCATE = "relocate"
SWEEP = "sweep"

# Statuses after apply.
DONE = "done"
CONFLICT = "conflict"   # no-clobber leftovers; a human resolves
SKIPPED = "skipped"


@dataclass(frozen=True)
class Action:
    kind: str
    src: str
    dst: str
    file_count: int = 0
    status: str = ""    # empty until applied
    note: str = ""


@dataclass(frozen=True)
class Plan:
    project: str
    actions: tuple[Action, ...]

    @property
    def empty(self) -> bool:
        return not self.actions


def build_plan(report: ProjectReport, m: DriveMap) -> Plan:
    actions: list[Action] = []
    for item in report.missing_control_plane:
        actions.append(Action(kind=BACKFILL, src="", dst=item))
    for found, canonical in report.drift:
        actions.append(Action(kind=RENAME, src=found, dst=canonical))
    for hit in report.relocations:
        actions.append(Action(kind=RELOCATE, src=hit.source, dst=hit.target, file_count=hit.file_count))
    for name, target in report.sweeps:
        actions.append(Action(kind=SWEEP, src=name, dst=target))
    return Plan(project=report.name, actions=tuple(actions))


# ------------------------------------------------------------------- apply

def apply_plan(drive_root: Path, project: Path, m: DriveMap, plan: Plan,
               only: set[str] | None = None) -> Plan:
    """Execute the plan; returns it with per-action statuses filled in."""
    applied: list[Action] = []
    order = {BACKFILL: 0, RENAME: 1, RELOCATE: 2, SWEEP: 3}
    for action in sorted(plan.actions, key=lambda a: order[a.kind]):
        if only and action.kind not in only:
            applied.append(replace(action, status=SKIPPED, note="filtered by --only"))
            continue
        if action.kind == BACKFILL:
            applied.append(_apply_backfill(project, m, action))
        elif action.kind == RENAME:
            applied.append(_apply_move(project, action, merge_into_existing=True))
        elif action.kind == RELOCATE:
            applied.append(_apply_move(project, action, merge_into_existing=True))
        elif action.kind == SWEEP:
            applied.append(_apply_sweep(project, action))
    result = Plan(project=plan.project, actions=tuple(applied))
    done = [a for a in result.actions if a.status == DONE]
    if done:
        append_log(drive_root, f"[{project.name}] conform: " +
                   "; ".join(f"{a.kind} {a.src or a.dst} -> {a.dst}" for a in done))
    return result


# ---- control plane ---------------------------------------------------------

_HAS_FRONT_MATTER = re.compile(r"^\s*---")  # same test Conform-Project.ps1 uses


def _conform_project_md_lines(m: DriveMap, leaf: str) -> list[str]:
    """The Conform-Project.ps1 stub (leaner than New-Project's - no Site/
    Zoning/Program sections, no folder map; Conform never invents metadata)."""
    display = re.sub(r"^\d{6}_", "", leaf)
    lines = list(FRONT_MATTER_HEAD)
    lines.append(f'project: "{display}"')
    lines += FRONT_MATTER_KEYS
    lines += [
        "",
        f"# {leaf}",
        "",
        "> Maintained by Architecture Studio skills and the project team. Facts only -",
        "> rationale lives in `decisions/`. The YAML front-matter above is the machine",
        "> mirror of the Identity + Code tables; keep them in agreement.",
        "> **Next:** run `/project-dossier` to fill in the project facts.",
        "",
        "## Identity", "",
        "| Field | Value |", "|-------|-------|",
        f"| Project | {display} |", "| Address / BBL | |", "| Client | |", "| Jurisdiction | |",
        "",
        "## Code", "",
        "<!-- Mirrors the machine contract in the front-matter. Change a value here -> change it there too. -->", "",
        "| Item | Value | Source | Date |", "|------|-------|--------|------|",
        "| Building code edition | | | |", "| Occupancy group | | | |", "| Construction type | | | |",
        "| Sprinklered | | | |", "| Stories | | | |", "| Building area (SF) | | | |", "| Frontage (ft) | | | |",
        "| Existing C-of-O occupant load | | | |", "| Existing exits | | | |",
        "| Place-of-assembly strategy | | | |", "| Tenancy | | | |",
        "",
        "## Decisions", "",
        "<!-- maintained by /decision - do not edit by hand -->", "",
        "| # | Decision | Status | Date |", "|---|----------|--------|------|",
    ]
    return lines


def _apply_backfill(project: Path, m: DriveMap, action: Action) -> Action:
    target = action.dst
    if target == m.project_file:
        path = project / m.project_file
        if not path.exists():
            write_crlf_no_bom(path, _conform_project_md_lines(m, project.name))
            return replace(action, status=DONE, note="created stub")
        raw = path.read_text(encoding="utf-8-sig")
        if _HAS_FRONT_MATTER.match(raw):
            return replace(action, status=SKIPPED, note="machine contract already present")
        head = list(FRONT_MATTER_HEAD)
        display = re.sub(r"^\d{6}_", "", project.name)
        head.append(f'project: "{display}"')
        head += FRONT_MATTER_KEYS
        write_crlf_no_bom(path, head + [""] + raw.splitlines())
        return replace(action, status=DONE, note="prepended machine contract; prose preserved")
    if target == m.decisions_dir:
        dec = project / m.decisions_dir
        dec.mkdir(parents=True, exist_ok=True)
        readme = dec / "README.md"
        if not readme.exists():
            write_crlf_no_bom(readme, decisions_readme_lines())
        return replace(action, status=DONE)
    if target == m.claude_file:
        path = project / m.claude_file
        if path.exists():
            return replace(action, status=SKIPPED, note="exists")
        write_crlf_no_bom(path, claude_md_lines(m))
        return replace(action, status=DONE)
    if target == m.analysis_dir:
        (project / m.analysis_dir).mkdir(parents=True, exist_ok=True)
        return replace(action, status=DONE)
    return replace(action, status=SKIPPED, note=f"unknown control-plane item '{target}'")


# ---- moves (renames + relocations share one engine) -------------------------

def _file_count(path: Path) -> int:
    total = 0
    for _r, _d, files in os.walk(path, followlinks=False):
        total += len(files)
    return total


def _remove_if_file_empty(path: Path) -> bool:
    if _file_count(path) != 0:
        return False
    for root, dirs, _files in os.walk(path, topdown=False, followlinks=False):
        for d in dirs:
            (Path(root) / d).rmdir()
    path.rmdir()
    return True


def _apply_move(project: Path, action: Action, merge_into_existing: bool) -> Action:
    src = project / action.src
    dst = project / action.dst
    if not src.is_dir():
        return replace(action, status=SKIPPED, note="source gone")

    # Empty duplicate: the canonical home already owns the artifact class.
    if _remove_if_file_empty(src):
        return replace(action, status=DONE, note="removed file-empty source")

    if src.resolve() == dst.resolve() and action.src != action.dst:
        # Case-only rename on a case-insensitive mount: two-step via temp.
        tmp = src.with_name(src.name + ".atlas-tmp")
        src.rename(tmp)
        tmp.rename(dst)
        return replace(action, status=DONE, note="case-only rename")

    if not dst.exists():
        dst.parent.mkdir(parents=True, exist_ok=True)
        src.rename(dst)
        return replace(action, status=DONE)

    if not merge_into_existing:
        return replace(action, status=CONFLICT, note="target exists")

    # Merge, never clobber: move each child whose name is free at the target.
    moved, left = 0, 0
    for child in list(src.iterdir()):
        target = dst / child.name
        if target.exists():
            left += 1
            continue
        child.rename(target)
        moved += 1
    if left == 0 and _remove_if_file_empty(src):
        return replace(action, status=DONE, note=f"merged {moved} item(s)")
    return replace(action, status=CONFLICT,
                   note=f"merged {moved}, {left} name collision(s) left in {action.src}")


def _apply_sweep(project: Path, action: Action) -> Action:
    src = project / action.src
    if not src.is_file():
        return replace(action, status=SKIPPED, note="source gone")
    dst_dir = project / action.dst.replace("\\", "/").rstrip("/")
    dst_dir.mkdir(parents=True, exist_ok=True)
    target = dst_dir / src.name
    if target.exists():
        return replace(action, status=CONFLICT, note="name exists at target")
    src.rename(target)
    return replace(action, status=DONE)
