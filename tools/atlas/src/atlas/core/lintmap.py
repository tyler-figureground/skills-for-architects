"""Validate the map itself: `atlas lint`.

Catches the bug classes the v1.1 ARCHITECTURE map actually shipped with:
an analysisDir pointing at an unblessed folder, the same child blessed in two
sections (Invoices), spelling drift inside the anti-drift file (PunchList vs
Punch List), and mixed numeric prefix widths that break sort order.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from .mapfile import DriveMap

# Levels: "error" = the map contradicts itself and tools may misbehave;
# "warn" = legal but suspicious, a human should look once.
ERROR = "error"
WARN = "warn"


@dataclass(frozen=True)
class Finding:
    level: str
    code: str
    message: str


def _first_segment(path: str) -> str:
    return path.replace("\\", "/").split("/", 1)[0]


def lint_map(m: DriveMap) -> list[Finding]:
    findings: list[Finding] = []
    ids = m.section_ids

    # -- sections ------------------------------------------------------------
    seen: set[str] = set()
    for s in m.sections:
        if s.id in seen:
            findings.append(Finding(ERROR, "DUP-SECTION", f"section '{s.id}' listed twice"))
        seen.add(s.id)
        if not re.match(r"^\d{2} ", s.id):
            findings.append(
                Finding(WARN, "SECTION-PREFIX", f"section '{s.id}' lacks a two-digit 'NN ' prefix")
            )

    # -- driftMap targets must be canonical sections --------------------------
    for src, dst in m.drift_map.items():
        if dst not in ids:
            findings.append(
                Finding(ERROR, "DRIFT-TARGET", f"driftMap '{src}' -> '{dst}': target is not a canonical section")
            )
        if "/" in dst or "\\" in dst:
            findings.append(
                Finding(ERROR, "DRIFT-IS-MOVE", f"driftMap '{src}' -> '{dst}': targets a path; moves belong in relocations (PS1 Rename-Item cannot move)")
            )

    # -- relocations targets must land somewhere blessed ----------------------
    cp_roots = {
        _first_segment(v) for v in m.control_plane.values() if isinstance(v, str) and v
    }
    for src, dst in m.relocations.items():
        head = _first_segment(dst)
        if head in ids:
            section = m.section(head)
            rest = dst.replace("\\", "/").removeprefix(head).lstrip("/")
            if rest and section is not None and rest not in section.children:
                # Check parent paths too: "10 Legal/Invoices" is blessed even if
                # a deeper target like "10 Legal/Invoices/2026" is not listed.
                parents = {c for c in section.children}
                if not any(rest.startswith(c + "/") or rest == c for c in parents):
                    findings.append(
                        Finding(WARN, "RELOC-UNBLESSED-CHILD", f"relocation '{src}' -> '{dst}': '{rest}' is not a blessed child of '{head}'")
                    )
        elif head in cp_roots:
            pass  # control-plane destination (.agent/handoff etc.)
        else:
            findings.append(
                Finding(ERROR, "RELOC-TARGET", f"relocation '{src}' -> '{dst}': target root '{head}' is neither a canonical section nor a control-plane dir")
            )

    # -- controlPlane.analysisDir must be a blessed path ----------------------
    if m.analysis_dir:
        head = _first_segment(m.analysis_dir)
        rest = m.analysis_dir.replace("\\", "/").removeprefix(head).lstrip("/")
        section = m.section(head)
        if section is None:
            findings.append(
                Finding(ERROR, "ANALYSIS-DIR", f"controlPlane.analysisDir '{m.analysis_dir}': '{head}' is not a canonical section")
            )
        elif rest and rest not in section.children:
            findings.append(
                Finding(ERROR, "ANALYSIS-DIR", f"controlPlane.analysisDir '{m.analysis_dir}': '{rest}' is not a blessed child of '{head}' (Add-Section cannot create it)")
            )

    # -- same child name blessed in two sections ------------------------------
    homes: dict[str, list[str]] = {}
    for s in m.sections:
        for child in s.children:
            leaf = child.replace("\\", "/").split("/")[-1]
            homes.setdefault(leaf, []).append(s.id)
    for leaf, in_sections in sorted(homes.items()):
        if len(in_sections) > 1:
            findings.append(
                Finding(WARN, "DUP-CHILD", f"'{leaf}' is blessed in {len(in_sections)} sections: {', '.join(in_sections)} - one artifact class, one home?")
            )

    # -- mixed numeric prefix widths inside one section ------------------------
    for s in m.sections:
        widths = set()
        for child in s.children:
            top = _first_segment(child)
            match = re.match(r"^(\d+) ", top)
            if match:
                widths.add(len(match.group(1)))
        if len(widths) > 1:
            findings.append(
                Finding(WARN, "MIXED-PREFIX", f"section '{s.id}' mixes numeric prefix widths {sorted(widths)}; sort order will lie")
            )

    return findings
