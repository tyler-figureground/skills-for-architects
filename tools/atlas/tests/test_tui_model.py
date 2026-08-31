from __future__ import annotations

from atlas.core.doctor import ProjectReport, RelocationHit
from atlas.core.mapfile import find_map, load_map
from atlas.tui.model import project_detail, project_rows, visible_rows


def test_rows_use_studio_language_and_stable_project_keys(fixture_drive):
    drive_map = load_map(find_map(fixture_drive))
    report = ProjectReport(
        name="260813_River Studio",
        status="unfiled",
        sections_present=3,
        unfiled=("survey.pdf",),
    )

    row = project_rows((report,), drive_map)[0]

    assert row.key == report.name
    assert row.health == "REVIEW"
    assert row.sections == "3/5"
    assert row.fixes == 0
    assert row.review == 1


def test_filter_matches_name_health_and_plain_language(fixture_drive):
    drive_map = load_map(find_map(fixture_drive))
    rows = project_rows(
        (
            ProjectReport("260813_Ready", "conform", 5),
            ProjectReport("260813_Fix", "drift", 3, missing_control_plane=("PROJECT.md",)),
            ProjectReport("260813_Loose", "unfiled", 4, unfiled=("notes.txt",)),
        ),
        drive_map,
    )

    assert [row.key for row in visible_rows(rows, query="ready")] == ["260813_Ready"]
    assert [row.key for row in visible_rows(rows, query="needs attention")] == [
        "260813_Fix",
        "260813_Loose",
    ]
    assert [row.key for row in visible_rows(rows, query="loose")] == ["260813_Loose"]


def test_sorting_uses_counts_but_retains_name_tiebreaker(fixture_drive):
    drive_map = load_map(find_map(fixture_drive))
    rows = project_rows(
        (
            ProjectReport("260813_Beta", "drift", 2, drift=(("Meetings", "11 Meetings"),)),
            ProjectReport(
                "260813_Alpha",
                "drift",
                2,
                missing_control_plane=("PROJECT.md", "CLAUDE.md"),
            ),
            ProjectReport("260813_Ready", "conform", 5),
        ),
        drive_map,
    )

    assert [row.key for row in visible_rows(rows)] == [
        "260813_Alpha",
        "260813_Beta",
        "260813_Ready",
    ]
    assert [row.key for row in visible_rows(rows, sort_column="fixes", reverse=True)] == [
        "260813_Alpha",
        "260813_Beta",
        "260813_Ready",
    ]


def test_project_detail_separates_repairs_from_human_review(fixture_drive):
    drive_map = load_map(find_map(fixture_drive))
    report = ProjectReport(
        name="260813_Clinic",
        status="drift",
        sections_present=2,
        missing_control_plane=("PROJECT.md",),
        drift=(("Meetings", "11 Meetings"),),
        relocations=(RelocationHit("08 OUT/Invoices", "10 Legal/Invoices", 4),),
        sweeps=(("HANDOFF-old.md", ".agent/handoff/"),),
        unfiled=("mystery.bin",),
    )
    row = project_rows((report,), drive_map)[0]

    detail = project_detail(row)

    assert "ATLAS CAN FIX" in detail
    assert "Backfill PROJECT.md" in detail
    assert "Rename Meetings -> 11 Meetings" in detail
    assert "Move 08 OUT/Invoices -> 10 Legal/Invoices (4 files)" in detail
    assert "REVIEW REQUIRED" in detail
    assert "Unfiled: mystery.bin" in detail
