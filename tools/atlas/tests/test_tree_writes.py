"""The core write surface the tree pulls on (ticket 21, ADR 0006).

Everything here is core: a Plan holding one Action, its Move Manifest, its
inverse, and the guard that decides whether it is still safe to apply. No TUI,
fixture drives only.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from atlas.cli import main

from atlas.core.conform import (
    WINDOWS_MAX_PATH,
    Guard,
    NotInvertible,
    apply_plan,
    build_plan,
    build_repair_plan,
    invert_plan,
)
from atlas.core.doctor import report_project
from atlas.core.scan import long_path, scan_drive

from conftest import FIXTURE_MAP, make_project, write_map


def plan_for(drive, name):
    inventory = scan_drive(drive)
    m = inventory.map
    inv = next(p for p in inventory.projects if p.name == name)
    return build_plan(report_project(inv, m), m, project=inv.path), inv, m


# ------------------------------------------------------- the Move Manifest


def test_rename_records_the_folder_it_moved(fixture_drive):
    make_project(
        fixture_drive, "260301_Drifty", sections=["01 Model", "Meetings"],
        files={"Meetings/kickoff.md": "notes"},
    )
    plan, inv, m = plan_for(fixture_drive, "260301_Drifty")
    result = apply_plan(fixture_drive, inv.path, m, plan, only={"rename"})

    action = next(a for a in result.actions if a.kind == "rename")
    assert [(mv.src, mv.dst, mv.is_dir) for mv in action.moved] == [
        ("Meetings", "11 Meetings", True)
    ]


def test_merge_records_each_child_it_actually_moved(fixture_drive):
    """A merge moves children one at a time, and only the ones whose name is
    free at the target. The manifest is what tells Atlas which those were."""
    make_project(
        fixture_drive, "260302_Merge",
        sections=["01 Model", "Meetings/Agendas", "11 Meetings"],
        files={
            "Meetings/b.md": "old-b",
            "Meetings/a.md": "old-a",
            "Meetings/Agendas/agenda.md": "old-agenda",
            "11 Meetings/a.md": "new-a",      # collision: never moved
        },
    )
    plan, inv, m = plan_for(fixture_drive, "260302_Merge")
    result = apply_plan(fixture_drive, inv.path, m, plan, only={"rename"})

    action = next(a for a in result.actions if a.kind == "rename")
    assert sorted((mv.src, mv.dst, mv.is_dir) for mv in action.moved) == [
        ("Meetings/Agendas", "11 Meetings/Agendas", True),
        ("Meetings/b.md", "11 Meetings/b.md", False),
    ]


def test_sweep_records_the_file_it_filed(fixture_drive):
    make_project(
        fixture_drive, "260303_Sweepy", sections=["01 Model"],
        files={"HANDOFF-roof-01.md": "x"},
    )
    plan, inv, m = plan_for(fixture_drive, "260303_Sweepy")
    result = apply_plan(fixture_drive, inv.path, m, plan, only={"sweep"})

    action = next(a for a in result.actions if a.kind == "sweep")
    assert [(mv.src, mv.dst, mv.is_dir) for mv in action.moved] == [
        ("HANDOFF-roof-01.md", ".agent/handoff/HANDOFF-roof-01.md", False)
    ]


def test_case_only_rename_records_its_move(fixture_drive):
    """The two-step-via-temp branch is still a move and still reversible."""
    write_map(fixture_drive, {**FIXTURE_MAP, "driftMap": {"01 model": "01 Model"}})
    make_project(
        fixture_drive, "260304_Case", sections=["01 model"],
        files={"01 model/model.rvt": "x"},
    )
    plan, inv, m = plan_for(fixture_drive, "260304_Case")
    result = apply_plan(fixture_drive, inv.path, m, plan, only={"rename"})

    action = next(a for a in result.actions if a.kind == "rename")
    assert action.status == "done"
    assert [(mv.src, mv.dst, mv.is_dir) for mv in action.moved] == [
        ("01 model", "01 Model", True)
    ]


# ------------------------------------------------------------ the inverse Plan


def test_inverting_a_rename_puts_the_folder_back(fixture_drive):
    make_project(
        fixture_drive, "260305_Undo", sections=["01 Model", "Meetings"],
        files={"Meetings/kickoff.md": "notes"},
    )
    plan, inv, m = plan_for(fixture_drive, "260305_Undo")
    applied = apply_plan(fixture_drive, inv.path, m, plan, only={"rename"})

    undo = apply_plan(fixture_drive, inv.path, m, invert_plan(applied))

    assert (inv.path / "Meetings" / "kickoff.md").read_text(encoding="utf-8") == "notes"
    assert not (inv.path / "11 Meetings").exists()
    assert all(a.status == "done" for a in undo.actions), undo.actions


def test_inverting_a_merge_sends_each_child_back_and_leaves_the_rest(fixture_drive):
    """The whole reason the manifest exists. A merge into an existing folder
    cannot be undone by moving the folder back - that would drag along whatever
    was already living there."""
    make_project(
        fixture_drive, "260306_UndoMerge",
        sections=["01 Model", "Meetings/Agendas", "11 Meetings"],
        files={
            "Meetings/b.md": "old-b",
            "Meetings/Agendas/agenda.md": "old-agenda",
            "11 Meetings/native.md": "was always here",
        },
    )
    plan, inv, m = plan_for(fixture_drive, "260306_UndoMerge")
    applied = apply_plan(fixture_drive, inv.path, m, plan, only={"rename"})
    assert next(a for a in applied.actions if a.kind == "rename").status == "done"

    undo = apply_plan(fixture_drive, inv.path, m, invert_plan(applied))

    assert all(a.status == "done" for a in undo.actions), undo.actions
    assert (inv.path / "Meetings" / "b.md").read_text(encoding="utf-8") == "old-b"
    assert (inv.path / "Meetings" / "Agendas" / "agenda.md").is_file()
    # The folder that was already there is untouched by the undo.
    assert (inv.path / "11 Meetings" / "native.md").read_text(encoding="utf-8") == "was always here"
    assert not (inv.path / "11 Meetings" / "b.md").exists()
    assert not (inv.path / "11 Meetings" / "Agendas").exists()


def test_a_backfill_cannot_be_inverted(fixture_drive):
    """Backfill creates; it never moves. There is no manifest to reverse, and
    Atlas refuses the whole Plan rather than performing a partial undo."""
    make_project(fixture_drive, "260307_Backfill", sections=["01 Model"])
    plan, inv, m = plan_for(fixture_drive, "260307_Backfill")
    applied = apply_plan(fixture_drive, inv.path, m, plan, only={"backfill"})
    assert any(a.status == "done" for a in applied.actions)

    with pytest.raises(NotInvertible, match="backfill"):
        invert_plan(applied)


def test_a_removed_file_empty_source_cannot_be_inverted(fixture_drive):
    """The empty-duplicate branch deletes rather than moves. Nothing in the
    manifest describes the folder chain it removed."""
    make_project(
        fixture_drive, "260308_EmptyDup",
        sections=["01 Model", "08 OUT/Invoices"],
    )
    plan, inv, m = plan_for(fixture_drive, "260308_EmptyDup")
    applied = apply_plan(fixture_drive, inv.path, m, plan, only={"relocate"})
    action = next(a for a in applied.actions if a.kind == "relocate")
    assert action.status == "done" and "file-empty" in action.note

    with pytest.raises(NotInvertible, match="moved nothing"):
        invert_plan(applied)


def test_a_conflict_cannot_be_inverted(fixture_drive):
    """A conflicted merge has a manifest, but the drive is in a state neither
    side of the move owns. Reversing half of it is not an undo."""
    make_project(
        fixture_drive, "260309_Conflicted",
        sections=["01 Model", "Meetings", "11 Meetings"],
        files={"Meetings/a.md": "old-a", "Meetings/b.md": "old-b",
               "11 Meetings/a.md": "new-a"},
    )
    plan, inv, m = plan_for(fixture_drive, "260309_Conflicted")
    applied = apply_plan(fixture_drive, inv.path, m, plan, only={"rename"})
    assert next(a for a in applied.actions if a.kind == "rename").status == "conflict"

    with pytest.raises(NotInvertible, match="conflict"):
        invert_plan(applied)


# --------------------------------------------------------- one-action Plans


def test_a_node_repair_is_the_action_the_full_plan_would_have_built(fixture_drive):
    """The tree invents no new action kinds (ADR 0006). Asserted against
    build_plan rather than trusted: the two must never diverge."""
    make_project(
        fixture_drive, "260310_Nodes",
        sections=["01 Model", "Meetings", "08 OUT/Invoices", "10 Legal"],
        files={"Meetings/kickoff.md": "z", "08 OUT/Invoices/inv.pdf": "y",
               "HANDOFF-roof-01.md": "h"},
    )
    plan, inv, m = plan_for(fixture_drive, "260310_Nodes")
    report = report_project(inv, m)

    for path in ("Meetings", "08 OUT/Invoices", "HANDOFF-roof-01.md", "PROJECT.md"):
        repair = build_repair_plan(report, m, path, project=inv.path)
        expected = [a for a in plan.actions if (a.src or a.dst) == path]
        assert repair.actions == tuple(expected), path
        assert len(repair.actions) == 1, path


def test_a_node_with_nothing_wrong_earns_no_action(fixture_drive):
    """Mapped is nothing to do; Unfiled is nobody's decision but a person's."""
    make_project(
        fixture_drive, "260311_Quiet",
        sections=["01 Model", "11 Meetings"],
        files={"Scratch/note.md": "mine"},
    )
    plan, inv, m = plan_for(fixture_drive, "260311_Quiet")
    report = report_project(inv, m)
    assert "Scratch" in report.unfiled

    for path in ("01 Model", "Scratch", "no/such/node"):
        assert build_repair_plan(report, m, path, project=inv.path).empty, path


# ---------------------------------------------------------------- the guards


def guards_for(drive, name, path):
    """A project-scope guard and an action-scope guard over the same repair."""
    inventory = scan_drive(drive)
    m = inventory.map
    inv = next(p for p in inventory.projects if p.name == name)
    report = report_project(inv, m)
    full = build_plan(report, m, project=inv.path)
    one = build_repair_plan(report, m, path, project=inv.path)
    return (Guard.for_project(drive, name, m, full),
            Guard.for_action(drive, name, m, one))


def test_a_guard_over_an_unchanged_project_is_fresh(fixture_drive):
    make_project(
        fixture_drive, "260312_Fresh", sections=["01 Model", "Meetings"],
        files={"Meetings/kickoff.md": "z"},
    )
    project_guard, action_guard = guards_for(fixture_drive, "260312_Fresh", "Meetings")

    assert project_guard.check(fixture_drive) is None
    assert action_guard.check(fixture_drive) is None


def test_both_guards_call_the_same_in_scope_divergence_stale(fixture_drive):
    """Run them side by side. Where the action's neighbourhood changed, the
    cheap guard must reach the same verdict as the expensive one."""
    project = make_project(
        fixture_drive, "260313_Raced", sections=["01 Model", "Meetings"],
        files={"Meetings/kickoff.md": "z"},
    )
    project_guard, action_guard = guards_for(fixture_drive, "260313_Raced", "Meetings")

    # Someone creates the destination between the preview and the confirmation.
    (project / "11 Meetings").mkdir()

    assert project_guard.check(fixture_drive) is not None
    assert action_guard.check(fixture_drive) is not None


def test_both_guards_notice_the_work_itself_changed(fixture_drive):
    project = make_project(
        fixture_drive, "260314_Gone", sections=["01 Model", "Meetings"],
        files={"Meetings/kickoff.md": "z"},
    )
    project_guard, action_guard = guards_for(fixture_drive, "260314_Gone", "Meetings")

    (project / "Meetings").rename(project / "11 Meetings")

    assert project_guard.check(fixture_drive) is not None
    assert action_guard.check(fixture_drive) is not None


def test_the_scoped_guard_ignores_a_change_the_action_cannot_touch(fixture_drive):
    """The asymmetry is the point of scoping, not a hole in it. A folder
    appearing at the project root cannot change what a relocate three levels
    away does, and a keystroke cannot afford to care."""
    project = make_project(
        fixture_drive, "260315_Elsewhere",
        sections=["01 Model", "08 OUT/Invoices", "10 Legal"],
        files={"08 OUT/Invoices/inv.pdf": "y"},
    )
    project_guard, action_guard = guards_for(
        fixture_drive, "260315_Elsewhere", "08 OUT/Invoices")
    assert action_guard.watched and all(
        rel in ("08 OUT", "10 Legal") for rel, _s, _e in action_guard.watched)

    (project / "ZZZ Scratch").mkdir()

    assert project_guard.check(fixture_drive) is not None
    assert action_guard.check(fixture_drive) is None


def test_a_sweep_watches_the_folder_it_files_into(fixture_drive):
    """A sweep's destination is a directory, not the swept item's new path. The
    guard has to watch the folder itself, or a file arriving there is invisible."""
    project = make_project(
        fixture_drive, "260316_SweepRace", sections=["01 Model"],
        files={"HANDOFF-roof-01.md": "mine", ".agent/handoff/keep.md": "x"},
    )
    _project_guard, action_guard = guards_for(
        fixture_drive, "260316_SweepRace", "HANDOFF-roof-01.md")
    assert sorted(rel for rel, _s, _e in action_guard.watched) == ["", ".agent/handoff"]

    (project / ".agent" / "handoff" / "HANDOFF-roof-01.md").write_text("theirs", encoding="utf-8")

    assert action_guard.check(fixture_drive) is not None


# ------------------------------------------------------- the path-length warning

LONG_A, LONG_B = "L" * 60, "M" * 60


def test_a_move_that_would_exceed_max_path_warns_at_preview(fixture_drive):
    """Ticket 19 found live over-MAX_PATH folders on the studio drive. A move
    can create one, so the length is computed while the plan is still a preview:
    deepest path under the source, re-hung under the destination."""
    write_map(fixture_drive, {**FIXTURE_MAP, "relocations": {
        "08 OUT/Invoices": f"10 Legal/{LONG_A}/{LONG_B}"}})
    project = make_project(
        fixture_drive, "260317_Long", sections=["01 Model", "08 OUT/Invoices", "10 Legal"])
    deep = project / "08 OUT" / "Invoices" / ("d" * 55)
    os.makedirs(long_path(deep), exist_ok=True)
    Path(long_path(deep / "invoice-for-the-client.pdf")).write_text("x", encoding="utf-8")

    plan, inv, m = plan_for(fixture_drive, "260317_Long")
    action = next(a for a in plan.actions if a.kind == "relocate")

    # The source is comfortably inside the limit where it sits today.
    assert len(str(deep / "invoice-for-the-client.pdf")) < WINDOWS_MAX_PATH
    assert action.path_length > WINDOWS_MAX_PATH
    assert action.path_warning


def test_a_move_inside_the_limit_does_not_warn(fixture_drive):
    make_project(
        fixture_drive, "260318_Short", sections=["01 Model", "Meetings"],
        files={"Meetings/kickoff.md": "z"},
    )
    plan, inv, m = plan_for(fixture_drive, "260318_Short")
    for action in plan.actions:
        assert action.path_length and not action.path_warning, action


# ------------------------------------------------------------- the CLI surface


def test_conform_json_carries_the_manifest_and_the_length(fixture_drive, capsys):
    """--json is one of the six consumers of Action. Widening the record has to
    keep it serialisable, and the path-length warning has to reach it."""
    make_project(
        fixture_drive, "260319_Json", sections=["01 Model", "Meetings"],
        files={"Meetings/kickoff.md": "z"},
    )
    assert main(["conform", "--drive", str(fixture_drive),
                 "--project", "260319_Json", "--apply", "--json"]) == 0

    payload = json.loads(capsys.readouterr().out)
    action = next(a for p in payload for a in p["actions"] if a["kind"] == "rename")
    assert action["moved"] == [
        {"src": "Meetings", "dst": "11 Meetings", "is_dir": True}
    ]
    assert action["path_length"] > 0
    assert action["path_warning"] is False


def test_conform_plan_shows_the_path_warning_to_a_person(fixture_drive, capsys):
    """A warning nobody reads is not a warning. It rides the plan line, and the
    plan still runs - Atlas warns, it never refuses (ADR 0006)."""
    write_map(fixture_drive, {**FIXTURE_MAP, "relocations": {
        "08 OUT/Invoices": f"10 Legal/{LONG_A}/{LONG_B}"}})
    project = make_project(
        fixture_drive, "260320_Warned",
        sections=["01 Model", "08 OUT/Invoices", "10 Legal"])
    deep = project / "08 OUT" / "Invoices" / ("d" * 55)
    os.makedirs(long_path(deep), exist_ok=True)
    Path(long_path(deep / "invoice-for-the-client.pdf")).write_text("x", encoding="utf-8")

    assert main(["conform", "--drive", str(fixture_drive),
                 "--project", "260320_Warned"]) == 1
    out = capsys.readouterr().out
    assert "> 260]" in out, out
