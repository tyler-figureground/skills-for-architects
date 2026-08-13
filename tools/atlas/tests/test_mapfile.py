from __future__ import annotations

import pytest

from atlas.core.mapfile import MapError, find_map, load_map

from conftest import FIXTURE_MAP, write_map


def test_load_map_parses_schema_v2(fixture_drive):
    m = load_map(find_map(fixture_drive))
    assert m.drive == "TESTDRIVE"
    assert m.version == "2.0"
    assert "11 Meetings" in m.section_ids
    assert m.drift_map["Meetings"] == "11 Meetings"
    # commentary keys stripped from relocations
    assert "_note" not in m.relocations
    assert m.relocations["08 OUT/Invoices"] == "10 Legal/Invoices"
    assert m.analysis_dir == "06 Research/Code"
    assert m.handoffs_dir == ".agent/handoff"


def test_find_map_ignores_missing_tools_dir(tmp_path):
    assert find_map(tmp_path) is None


def test_load_map_rejects_missing_keys(tmp_path):
    drive = tmp_path / "D"
    write_map(drive, {"drive": "D", "sections": []})  # no version
    with pytest.raises(MapError):
        load_map(find_map(drive))


def test_control_plane_defaults_match_ps1(tmp_path):
    drive = tmp_path / "D"
    write_map(drive, {"drive": "D", "version": "1", "sections": [{"id": "01 A"}]})
    m = load_map(find_map(drive))
    assert m.project_file == "PROJECT.md"
    assert m.decisions_dir == "decisions"
    assert m.claude_file == "CLAUDE.md"
