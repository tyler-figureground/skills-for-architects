"""PROJECT.md / control-plane file generation.

Generated files preserve the machine-facing encoding contract: UTF-8 without a
BOM, CRLF line endings, and a trailing newline. Atlas 0.2 owns complete intake
metadata; legacy PowerShell writers may emit only blank compatibility stubs.
The canonical-map section remains marker-wrapped so Doctor can regenerate it
idempotently.
"""

from __future__ import annotations

import json
from pathlib import Path

from .intake import ContactSnapshot, ResolvedProjectIntake
from .mapfile import DriveMap

MAP_BEGIN = "<!-- atlas:map-begin -->"
MAP_END = "<!-- atlas:map-end -->"

# The machine contract - identical in New-Project.ps1 and Conform-Project.ps1.
# Bare keys, no inline comments (a tiny YAML fallback parser reads comments as
# values), and never a BOM ahead of the opening '---'.
FRONT_MATTER_HEAD = (
    "---",
    "# Machine contract - tool-authoritative project facts. Norma and other",
    "# architect skills read THIS YAML block, not the prose below. A blank field",
    "# is ignored, not assumed; Norma adopts this project only once jurisdiction /",
    "# occupancy_group / edition are real. Run /project-dossier to fill it in, and",
    "# keep it in sync with the Identity + Code tables (the human mirror).",
)
FRONT_MATTER_KEYS = (
    "jurisdiction:",
    "edition:",
    "occupancy_group:",
    "construction_type:",
    "sprinklered:",
    "stories:",
    "building_area_sf:",
    "frontage_ft:",
    "existing_co_occupant_load:",
    "existing_exits:",
    "place_of_assembly_strategy:",
    "tenancy:",
    "---",
)


def _crlf_bytes(lines: list[str]) -> bytes:
    return ("\r\n".join(lines) + "\r\n").encode("utf-8")


def write_crlf_no_bom(path: Path, lines: list[str]) -> None:
    """The PS1 writer's exact byte behavior: WriteAllLines = line + CRLF each."""
    path.write_bytes(_crlf_bytes(lines))


def create_crlf_no_bom(path: Path, lines: list[str]) -> bool:
    """Create a control file exclusively; never replace a concurrent arrival."""

    try:
        with path.open("xb") as stream:
            stream.write(_crlf_bytes(lines))
    except FileExistsError:
        return False
    return True


def _yaml(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def _table(value: str) -> str:
    escaped = value.replace("\\", "\\\\").replace("|", r"\|")
    return " ".join(escaped.splitlines()).strip()


def blank_intake_front_matter(project: str) -> list[str]:
    """Blank expanded intake contract for legacy-project conform stubs."""

    lines = [
        f"project: {_yaml(project)}",
        "address:",
        "address_street:",
        "address_unit:",
        "address_city:",
        "address_state:",
        "address_postal_code:",
        "description:",
        "project_use_case:",
        "project_use_case_category:",
    ]
    for role in ("billing", "client"):
        lines += [
            f"{role}_contact_id:",
            f"{role}_contact_name:",
            f"{role}_contact_email:",
            f"{role}_contact_phone:",
            f"{role}_contact_company:",
            f"{role}_contact_address:",
        ]
    return lines + list(FRONT_MATTER_KEYS)


def blank_intake_identity_rows(project: str) -> list[str]:
    return [
        f"| Project | {_table(project)} |",
        "| Address / BBL | |",
        "| Project Use Case | |",
        "| Client | |",
        "| Billing Contact | |",
        "| Billing Email | |",
        "| Billing Phone | |",
        "| Billing Company | |",
        "| Billing Address | |",
        "| Client Contact | |",
        "| Client Email | |",
        "| Client Phone | |",
        "| Client Company | |",
        "| Client Address | |",
        "| Jurisdiction | |",
        "| Virtual tour | |",
        "| Descriptor | |",
        "| Created | |",
    ]


def _contact_front_matter(role: str, contact: ContactSnapshot) -> list[str]:
    return [
        f"{role}_contact_id: {_yaml(contact.id)}",
        f"{role}_contact_name: {_yaml(contact.full_name)}",
        f"{role}_contact_email: {_yaml(contact.email)}",
        f"{role}_contact_phone: {_yaml(contact.phone)}",
        f"{role}_contact_company: {_yaml(contact.company)}",
        f"{role}_contact_address: {_yaml(contact.address)}",
    ]


def project_md_lines(m: DriveMap, folder_name: str, intake: ResolvedProjectIntake) -> list[str]:
    name = intake.project_name
    desc = intake.description
    created = intake.request.created
    full_address = intake.project_address.formatted
    lines: list[str] = []
    lines += FRONT_MATTER_HEAD
    lines += [
        f"project: {_yaml(name)}",
        f"address: {_yaml(full_address)}",
        f"address_street: {_yaml(intake.project_address.street)}",
        f"address_unit: {_yaml(intake.project_address.unit)}",
        f"address_city: {_yaml(intake.project_address.city)}",
        f"address_state: {_yaml(intake.project_address.state)}",
        f"address_postal_code: {_yaml(intake.project_address.postal_code)}",
        f"description: {_yaml(desc)}",
        f"project_use_case: {_yaml(intake.project_use_case.display)}",
        f"project_use_case_category: {_yaml(intake.project_use_case.category)}",
    ]
    lines += _contact_front_matter("billing", intake.billing_contact)
    lines += _contact_front_matter("client", intake.client_contact)
    lines += FRONT_MATTER_KEYS
    lines += [
        "",
        f"# {folder_name}",
        "",
        "> Maintained by Architecture Studio skills and the project team. Facts only -",
        "> rationale lives in `decisions/`. The YAML front-matter above is the machine",
        "> mirror of the Identity + Code tables; keep them in agreement.",
        "> **Next:** run `/project-dossier` to fill in the project facts.",
        "",
        "## Identity",
        "",
        "| Field | Value |",
        "|-------|-------|",
        f"| Project | {_table(name)} |",
        f"| Address / BBL | {_table(full_address)} |",
        f"| Project Use Case | {_table(intake.project_use_case.display)} |",
        f"| Client | {_table(intake.client_contact.full_name)} |",
        f"| Billing Contact | {_table(intake.billing_contact.full_name)} |",
        f"| Billing Email | {_table(intake.billing_contact.email)} |",
        f"| Billing Phone | {_table(intake.billing_contact.phone)} |",
        f"| Billing Company | {_table(intake.billing_contact.company)} |",
        f"| Billing Address | {_table(intake.billing_contact.address)} |",
        f"| Client Contact | {_table(intake.client_contact.full_name)} |",
        f"| Client Email | {_table(intake.client_contact.email)} |",
        f"| Client Phone | {_table(intake.client_contact.phone)} |",
        f"| Client Company | {_table(intake.client_contact.company)} |",
        f"| Client Address | {_table(intake.client_contact.address)} |",
        "| Jurisdiction | |",
        "| Virtual tour | |",
        f"| Descriptor | {_table(desc)} |",
        f"| Created | {created.strftime('%Y-%m-%d')} |",
        f"| Drive | {m.drive} |",
        "| Status | Active |",
        "",
        "## Site",
        "",
        "<!-- site-planner skills append here: climate, flood, transit, demographics, context -->",
        "",
        "## Zoning",
        "",
        "<!-- zoning skills append here: district, FAR, envelope, overlays, landmark status -->",
        "",
        "## Program",
        "",
        "<!-- programming skills append here: headcount, space program, occupant loads -->",
        "",
        "## Code",
        "",
        "<!-- Mirrors the machine contract in the front-matter. Change a value here -> change it there too. -->",
        "",
        "| Item | Value | Source | Date |",
        "|------|-------|--------|------|",
        "| Building code edition | | | |",
        "| Occupancy group | | | |",
        "| Construction type | | | |",
        "| Sprinklered | | | |",
        "| Stories | | | |",
        "| Building area (SF) | | | |",
        "| Frontage (ft) | | | |",
        "| Existing C-of-O occupant load | | | |",
        "| Existing exits | | | |",
        "| Place-of-assembly strategy | | | |",
        "| Tenancy | | | |",
        "",
        "## Decisions",
        "",
        "<!-- maintained by /decision - do not edit by hand -->",
        "",
        "| # | Decision | Status | Date |",
        "|---|----------|--------|------|",
        "",
    ]
    lines += canonical_map_lines(m)
    return lines


def canonical_map_lines(m: DriveMap) -> list[str]:
    """The regenerable 'Where things go' block, marker-wrapped for --fix-project-md."""
    lines = [
        MAP_BEGIN,
        "## Where things go (canonical map)",
        "",
        "Sections tagged **[seed]** exist now. Everything else is created on demand:",
        "double-click `_tools\\Add-Section.bat`, pick this project, pick the folder.",
        "**Do not hand-create canonical folders** - use Add-Section so names never drift.",
        "",
    ]
    for section in m.sections:
        tag = " _[seed]_" if section.seed else " _[on demand]_"
        lines.append(f"- **{section.id}**{tag}")
        for child in section.children:
            lines.append(f"  - {child}")
    lines += [
        "",
        f"_Naming: {m.project_naming}. Generated by Atlas._",
        MAP_END,
    ]
    return lines


def decisions_readme_lines() -> list[str]:
    return [
        "# Decisions",
        "",
        "ADR-style decision records for this project - one per file (`NNNN-slug.md`),",
        "maintained by the `/decision` skill. Rationale lives here; current facts live",
        "in `../PROJECT.md`.",
    ]


def claude_md_lines(m: DriveMap) -> list[str]:
    return [
        "# Architecture project workspace",
        "",
        "Project facts live in `PROJECT.md` (the YAML machine contract every architect",
        "skill reads - most importantly Norma, which scopes code answers from it).",
        "Decisions live in `decisions/`. Norma writes cited code analyses to",
        f"`{m.analysis_dir}`.",
        "",
        "Start with `/project-dossier` to fill in `PROJECT.md`, then run `/code-analysis`,",
        "`/egress`, `/ibc`, etc. from this folder.",
    ]
