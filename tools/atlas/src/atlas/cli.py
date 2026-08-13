"""Atlas CLI - every TUI capability as a subcommand; --json is the agent interface.

Exit codes: 0 = clean, 1 = findings/pending work, 2 = error.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import __version__
from .core.doctor import report_drive, report_to_dict
from .core.lintmap import lint_map
from .core.mapfile import MapError, find_map, load_map
from .core.scan import DEFAULT_MOUNT_ROOT, discover_drives, scan_drive


def _resolve_drive(arg: str | None) -> Path:
    if arg:
        root = Path(arg)
        if not find_map(root):
            raise SystemExit(f"error: no _tools/*-map.json under {root}")
        return root
    cwd = Path.cwd()
    for candidate in (cwd, *cwd.parents):
        if find_map(candidate):
            return candidate
    drives = discover_drives()
    if len(drives) == 1:
        return drives[0]
    if not drives:
        raise SystemExit(f"error: no mapped drives found under {DEFAULT_MOUNT_ROOT}; pass --drive")
    names = ", ".join(d.name for d in drives)
    raise SystemExit(f"error: multiple mapped drives ({names}); pass --drive")


def cmd_lint(args: argparse.Namespace) -> int:
    root = _resolve_drive(args.drive)
    try:
        drive_map = load_map(find_map(root))
    except MapError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    findings = lint_map(drive_map)
    if args.json:
        print(json.dumps([f.__dict__ for f in findings], indent=2))
    else:
        print(f"map: {drive_map.path} (v{drive_map.version})")
        if not findings:
            print("lint: clean")
        for f in findings:
            print(f"  {f.level.upper():5} {f.code:22} {f.message}")
    return 1 if any(f.level == "error" for f in findings) else 0


def cmd_doctor(args: argparse.Namespace) -> int:
    root = _resolve_drive(args.drive)
    try:
        report = report_drive(scan_drive(root))
    except (MapError, FileNotFoundError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(report_to_dict(report), indent=2))
    else:
        counts = report.summary()
        print(f"{report.drive} (map v{report.map_version})  "
              f"{counts['conform']} conform / {counts['drift']} drift / "
              f"{counts['unfiled']} unfiled / {counts['stub']} stub")
        for p in report.projects:
            print(f"\n[{p.status.upper():7}] {p.name}  ({p.sections_present} sections)")
            for item in p.missing_control_plane:
                print(f"    control-plane missing: {item}")
            for src, dst in p.drift:
                print(f"    drift: {src} -> {dst}")
            for h in p.relocations:
                print(f"    relocation pending: {h.source} -> {h.target} ({h.file_count} files)")
            for name, dst in p.sweeps:
                print(f"    sweep pending: {name} -> {dst}")
            for name in p.unfiled:
                print(f"    unfiled: {name}")
    pending = any(p.actionable or p.unfiled for p in report.projects)
    return 1 if pending else 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="atlas", description="Map-driven studio drive tooling.")
    parser.add_argument("--version", action="version", version=f"atlas {__version__}")
    sub = parser.add_subparsers(dest="command")

    for name, fn, help_text in (
        ("lint", cmd_lint, "validate the drive's map file"),
        ("doctor", cmd_doctor, "read-only drive-wide conformance report"),
    ):
        p = sub.add_parser(name, help=help_text)
        p.add_argument("--drive", help="drive root (default: walk up from cwd, else auto-discover)")
        p.add_argument("--json", action="store_true", help="machine-readable output")
        p.set_defaults(fn=fn)

    args = parser.parse_args(argv)
    if args.command is None:
        from .tui.app import run_tui  # lazy: textual import only when needed
        return run_tui()
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
