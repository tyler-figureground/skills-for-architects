"""Read-only drive/project inventory.

Scans are dirent-driven (names + is_dir), never mtime-heavy: the Google Drive
mount hydrates placeholders on stat, and a full-tree stat storm makes a 15-project
drive take minutes. File counts recurse only into relocation-source folders,
which are small by construction.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from .mapfile import DriveMap, find_map, load_map

DEFAULT_MOUNT_ROOT = Path(os.environ.get("ATLAS_MOUNT_ROOT", r"G:\Shared drives"))


@dataclass(frozen=True)
class Entry:
    name: str
    is_dir: bool


@dataclass(frozen=True)
class ProjectInventory:
    path: Path
    name: str
    root_entries: tuple[Entry, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class DriveInventory:
    root: Path
    map: DriveMap
    projects: tuple[ProjectInventory, ...]


def discover_drives(mount_root: Path = DEFAULT_MOUNT_ROOT) -> list[Path]:
    """Drives under the mount that carry a map file."""
    if not mount_root.is_dir():
        return []
    return [d for d in sorted(mount_root.iterdir()) if d.is_dir() and find_map(d)]


def is_project_dir(name: str) -> bool:
    """Same exclusion rule the PS1 tools use: no '_' prefix, no '00 ' prefix."""
    return not (name.startswith("_") or name.startswith("00 ") or name.startswith("."))


def list_entries(path: Path) -> tuple[Entry, ...]:
    try:
        with os.scandir(path) as it:
            return tuple(
                Entry(name=e.name, is_dir=e.is_dir(follow_symlinks=False)) for e in it
            )
    except OSError:
        return ()


def scan_drive(drive_root: Path) -> DriveInventory:
    map_path = find_map(drive_root)
    if map_path is None:
        raise FileNotFoundError(f"no _tools/*-map.json under {drive_root}")
    drive_map = load_map(map_path)

    projects: list[ProjectInventory] = []
    for entry in list_entries(drive_root):
        if not entry.is_dir or not is_project_dir(entry.name):
            continue
        project_path = drive_root / entry.name
        projects.append(
            ProjectInventory(
                path=project_path,
                name=entry.name,
                root_entries=list_entries(project_path),
            )
        )
    return DriveInventory(root=drive_root, map=drive_map, projects=tuple(projects))


def count_files(path: Path) -> int:
    """Recursive file count; never follows junctions/symlinks."""
    total = 0
    for _root, dirs, files in os.walk(path, followlinks=False):
        total += len(files)
    return total
