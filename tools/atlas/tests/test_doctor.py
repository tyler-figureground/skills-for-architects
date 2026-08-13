from __future__ import annotations

from atlas.core.doctor import report_drive, report_to_dict
from atlas.core.scan import scan_drive

from conftest import make_project


def project_report(drive, name):
    report = report_drive(scan_drive(drive))
    return next(p for p in report.projects if p.name == name)


def full_control_plane(files=None):
    base = {
        "PROJECT.md": "---\nproject: x\n---\n",
        "CLAUDE.md": "# workspace\n",
        "decisions/README.md": "# Decisions\n",
        "06 Research/Code/.keep": "",
    }
    base.update(files or {})
    return base


def test_conform_project_reports_conform(fixture_drive):
    make_project(
        fixture_drive, "260101_Test-House",
        sections=["01 Model", "06 Research", "08 OUT", "11 Meetings"],
        files=full_control_plane(),
    )
    p = project_report(fixture_drive, "260101_Test-House")
    assert p.status == "conform"
    assert not p.actionable


def test_missing_control_plane_is_drift(fixture_drive):
    make_project(fixture_drive, "260102_Bare-House", sections=["01 Model"])
    p = project_report(fixture_drive, "260102_Bare-House")
    assert p.status == "drift"
    assert "PROJECT.md" in p.missing_control_plane
    assert "decisions" in p.missing_control_plane


def test_stub_project(fixture_drive):
    make_project(fixture_drive, "260103_Stub", files={"note.gdoc": "x"})
    p = project_report(fixture_drive, "260103_Stub")
    assert p.status == "stub"
    assert p.unfiled == ("note.gdoc",)


def test_drift_folder_detected_case_insensitive(fixture_drive):
    make_project(
        fixture_drive, "260104_Drifty",
        sections=["01 Model", "meetings"],
        files=full_control_plane(),
    )
    p = project_report(fixture_drive, "260104_Drifty")
    assert ("meetings", "11 Meetings") in p.drift
    assert p.status == "drift"


def test_relocation_source_counted(fixture_drive):
    make_project(
        fixture_drive, "260105_Reloc",
        sections=["01 Model", "08 OUT/Invoices"],
        files=full_control_plane({"08 OUT/Invoices/inv-001.pdf": "x"}),
    )
    p = project_report(fixture_drive, "260105_Reloc")
    hits = {(h.source, h.target, h.file_count) for h in p.relocations}
    assert ("08 OUT/Invoices", "10 Legal/Invoices", 1) in hits


def test_handoff_sweep_matches_glob_and_is_not_unfiled(fixture_drive):
    make_project(
        fixture_drive, "260106_Sweepy",
        sections=["01 Model"],
        files=full_control_plane({"HANDOFF-roof-01.md": "x"}),
    )
    p = project_report(fixture_drive, "260106_Sweepy")
    assert ("HANDOFF-roof-01.md", ".agent/handoff/") in p.sweeps
    assert "HANDOFF-roof-01.md" not in p.unfiled


def test_case_only_renamed_source_is_not_a_pending_relocation(fixture_drive, tmp_path):
    # Regression: on case-insensitive mounts, Path.is_dir() matches the RENAMED
    # target ("Change Orders") when probing the old source ("change Orders"),
    # reporting a phantom pending relocation forever. Exact-case probe required.
    import copy
    import json

    from conftest import FIXTURE_MAP, write_map

    data = copy.deepcopy(FIXTURE_MAP)
    data["relocations"]["08 OUT/change Orders"] = "08 OUT/Change Orders"
    write_map(fixture_drive, data)
    make_project(
        fixture_drive, "260109_Cased",
        sections=["01 Model", "08 OUT/Change Orders"],  # already renamed on disk
        files=full_control_plane(),
    )
    p = project_report(fixture_drive, "260109_Cased")
    assert not any(h.source == "08 OUT/change Orders" for h in p.relocations), p.relocations


def test_tolerated_root_files_not_unfiled(fixture_drive):
    make_project(
        fixture_drive, "260107_Ledger",
        sections=["01 Model"],
        files=full_control_plane({"jdp-time-ledger.ndjson": "{}", "desktop.ini": ""}),
    )
    p = project_report(fixture_drive, "260107_Ledger")
    assert p.unfiled == ()


def test_report_json_shape(fixture_drive):
    make_project(fixture_drive, "260108_Any", sections=["01 Model"])
    d = report_to_dict(report_drive(scan_drive(fixture_drive)))
    assert d["drive"] == "TESTDRIVE"
    assert {"conform", "drift", "unfiled", "stub"} <= set(d["summary"])
    (proj,) = [p for p in d["projects"] if p["name"] == "260108_Any"]
    assert set(proj) == {
        "name", "status", "sections_present", "missing_control_plane",
        "drift", "relocations", "sweeps", "unfiled",
    }


def test_underscore_and_00_dirs_excluded(fixture_drive):
    make_project(fixture_drive, "_Archived Projects", sections=["01 Model"])
    make_project(fixture_drive, "00 Templates")
    report = report_drive(scan_drive(fixture_drive))
    names = {p.name for p in report.projects}
    assert "_Archived Projects" not in names
    assert "00 Templates" not in names
