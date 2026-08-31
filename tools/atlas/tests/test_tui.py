"""TUI pilot smoke tests - the wizards drive the same core the CLI uses, so
these verify wiring, not logic (logic is covered in test_ops/test_conform)."""

from __future__ import annotations

import copy
from dataclasses import replace
from datetime import date
from threading import Event

import atlas.tui.app as tui_app
from atlas.core.conform import SKIPPED, Plan
from atlas.core.mapfile import find_map, load_map
from atlas.core.ops import new_project
from textual.widgets import Button, DataTable, Input, ListView, SelectionList, Static

from atlas.tui.app import AddSectionModal, AtlasApp, NewProjectModal, ResultModal

from conftest import FIXTURE_MAP, make_project, write_map


async def settle(app: AtlasApp, pilot) -> None:
    """Wait for a worker and any refresh worker it schedules."""

    for _ in range(3):
        await app.workers.wait_for_complete()
        await pilot.pause()


async def test_tui_boots_and_lists_projects(fixture_drive):
    m = load_map(find_map(fixture_drive))
    new_project(fixture_drive, m, "Alpha", created=date(2026, 8, 13))
    make_project(fixture_drive, "260813_Beta", sections=["01 Model"])

    app = AtlasApp(fixture_drive)
    async with app.run_test() as pilot:
        await settle(app, pilot)
        table = app.query_one("#projects")
        assert table.row_count == 2
        assert "TESTDRIVE" in app.sub_title


async def test_new_project_wizard_creates_on_disk(fixture_drive):
    app = AtlasApp(fixture_drive)
    async with app.run_test() as pilot:
        await settle(app, pilot)
        await pilot.press("n")
        await pilot.pause()
        assert isinstance(app.screen, NewProjectModal)
        app.screen.query_one("#name").value = "Wizard House"
        app.screen.query_one("#desc").value = "ADU"
        await pilot.pause()
        await pilot.click("#ok")
        await settle(app, pilot)

    stamp = date.today().strftime("%y%m%d")
    created = fixture_drive / f"{stamp}_Wizard House-ADU"
    assert created.is_dir()
    assert (created / "PROJECT.md").is_file()
    assert (created / "11 Meetings").is_dir()


async def test_conform_modal_applies_plan(fixture_drive):
    make_project(
        fixture_drive, "260813_Fixit", sections=["01 Model", "Meetings"],
        files={"Meetings/kickoff.md": "x"},
    )
    app = AtlasApp(fixture_drive)
    async with app.run_test() as pilot:
        await settle(app, pilot)
        await pilot.press("f")
        await pilot.pause()
        await pilot.click("#ok")
        await settle(app, pilot)

    project = fixture_drive / "260813_Fixit"
    assert (project / "11 Meetings" / "kickoff.md").is_file()
    assert (project / "PROJECT.md").is_file()


async def test_filter_is_fast_and_escape_restores_all_projects(fixture_drive):
    make_project(fixture_drive, "260813_Alpha", sections=["01 Model"])
    make_project(fixture_drive, "260813_Beta", sections=["01 Model"])
    app = AtlasApp(fixture_drive)

    async with app.run_test() as pilot:
        await settle(app, pilot)
        await pilot.press("/")
        filter_input = app.query_one("#filter", Input)
        assert filter_input.display
        await pilot.press("b", "e", "t", "a")
        await pilot.pause()
        assert app.query_one("#projects", DataTable).row_count == 1
        assert "Beta" in str(app.query_one("#detail-title", Static).content)

        await pilot.press("escape")
        await pilot.pause()
        assert not filter_input.display
        assert app.query_one("#projects", DataTable).row_count == 2


async def test_enter_opens_project_health_and_escape_closes(fixture_drive):
    make_project(
        fixture_drive,
        "260813_Review",
        sections=["01 Model"],
        files={"loose.pdf": "x"},
    )
    app = AtlasApp(fixture_drive)

    async with app.run_test() as pilot:
        await settle(app, pilot)
        await pilot.press("enter")
        await pilot.pause()
        assert isinstance(app.screen, ResultModal)
        assert "Project health" in str(app.screen.query_one(".dialog-title", Static).content)

        await pilot.press("escape")
        await pilot.pause()
        assert app.screen is app.screen_stack[0]


async def test_add_folders_requires_a_selection(fixture_drive):
    make_project(fixture_drive, "260813_Add", sections=["01 Model"])
    app = AtlasApp(fixture_drive)

    async with app.run_test() as pilot:
        await settle(app, pilot)
        await pilot.press("a")
        await settle(app, pilot)
        assert isinstance(app.screen, AddSectionModal)
        create = app.screen.query_one("#ok", Button)
        assert create.disabled

        choices = app.screen.query_one(SelectionList)
        choices.select(choices.get_option_at_index(0).value)
        await pilot.pause()
        assert not create.disabled


async def test_scan_failure_stays_visible_and_does_not_crash(fixture_drive, monkeypatch):
    def fail_scan(_root):
        raise PermissionError("shared drive unavailable")

    monkeypatch.setattr("atlas.tui.app.scan_drive", fail_scan)
    app = AtlasApp(fixture_drive)

    async with app.run_test() as pilot:
        await settle(app, pilot)
        operation = str(app.query_one("#operation", Static).content)
        assert "shared drive unavailable" in operation
        assert "Press r to retry" in operation
        assert app.check_action("new_project", ()) is None


async def test_back_reaches_single_drive_picker_without_reopening(fixture_drive, monkeypatch):
    monkeypatch.setattr("atlas.tui.app.discover_drives", lambda: [fixture_drive])
    app = AtlasApp(fixture_drive)

    async with app.run_test() as pilot:
        await settle(app, pilot)
        await pilot.press("escape")
        await pilot.pause()
        assert app.query_one("#drives", ListView).display
        assert app._inventory is None


async def test_back_during_slow_scan_ignores_late_result(fixture_drive, monkeypatch):
    real_scan = tui_app.scan_drive
    started = Event()
    release = Event()

    def slow_scan(root):
        started.set()
        release.wait(timeout=2)
        return real_scan(root)

    monkeypatch.setattr(tui_app, "scan_drive", slow_scan)
    monkeypatch.setattr(tui_app, "discover_drives", lambda: [fixture_drive])
    app = AtlasApp(fixture_drive)

    async with app.run_test() as pilot:
        await pilot.pause()
        assert started.wait(timeout=1)
        await pilot.press("escape")
        await pilot.pause()
        release.set()
        await settle(app, pilot)
        assert app.query_one("#drives", ListView).display
        assert not app.query_one("#workspace").display
        assert app._inventory is None


async def test_failed_refresh_keeps_diagnosis_but_disables_mutation(fixture_drive, monkeypatch):
    make_project(fixture_drive, "260813_Stale", sections=["01 Model"])
    app = AtlasApp(fixture_drive)

    async with app.run_test() as pilot:
        await settle(app, pilot)
        assert app._inventory_fresh

        monkeypatch.setattr(tui_app, "scan_drive", lambda _root: (_ for _ in ()).throw(PermissionError("offline")))
        await pilot.press("r")
        await settle(app, pilot)

        assert app.query_one("#projects", DataTable).row_count == 1
        assert not app._inventory_fresh
        assert app.check_action("conform", ()) is None
        assert "offline" in str(app.query_one("#operation", Static).content)


async def test_busy_state_hides_palette_mutations_and_direct_actions(fixture_drive):
    make_project(fixture_drive, "260813_Busy", sections=["01 Model"])
    app = AtlasApp(fixture_drive)

    async with app.run_test() as pilot:
        await settle(app, pilot)
        app._busy = True
        app._work_kind = "operation"
        commands = {command.title for command in app.get_system_commands(app.screen)}
        app.action_conform()
        await pilot.pause()

        assert "Conform project" not in commands
        assert app.screen is app.screen_stack[0]


async def test_add_modal_fits_and_focuses_choices_at_80_by_24(fixture_drive):
    make_project(fixture_drive, "260813_Compact", sections=[])
    app = AtlasApp(fixture_drive)

    async with app.run_test(size=(80, 24)) as pilot:
        await settle(app, pilot)
        await pilot.press("a")
        await settle(app, pilot)
        assert isinstance(app.screen, AddSectionModal)
        choices = app.screen.query_one(SelectionList)
        actions = app.screen.query_one(".actions")
        assert app.focused is choices
        assert actions.region.bottom <= app.size.height
        assert choices.region.height > 0


async def test_add_folders_does_not_recreate_deleted_project(fixture_drive):
    project = make_project(fixture_drive, "260813_Deleted", sections=[])
    app = AtlasApp(fixture_drive)

    async with app.run_test() as pilot:
        await settle(app, pilot)
        await pilot.press("a")
        await settle(app, pilot)
        choices = app.screen.query_one(SelectionList)
        choices.select(choices.get_option_at_index(0).value)
        await pilot.pause()
        project.rmdir()
        await pilot.click("#ok")
        await settle(app, pilot)

        assert app._last_result is not None
        assert app._last_result.title == "Add-folders plan changed"
        assert not project.exists()


async def test_new_project_refuses_changed_drive_map(fixture_drive):
    app = AtlasApp(fixture_drive)

    async with app.run_test() as pilot:
        await settle(app, pilot)
        await pilot.press("n")
        app.screen.query_one("#name", Input).value = "Changed Map"
        await pilot.pause()
        changed_map = copy.deepcopy(FIXTURE_MAP)
        changed_map["version"] = "2.1"
        write_map(fixture_drive, changed_map)
        await pilot.click("#ok")
        await settle(app, pilot)

        assert app._last_result is not None
        assert app._last_result.title == "Project plan changed"
        assert not any(path.name.endswith("_Changed Map") for path in fixture_drive.iterdir())


async def test_marked_projects_share_one_safe_conform_plan(fixture_drive):
    for name in ("260813_Alpha", "260813_Beta"):
        make_project(
            fixture_drive,
            name,
            sections=["01 Model", "Meetings"],
            files={"Meetings/kickoff.md": name},
        )
    app = AtlasApp(fixture_drive)

    async with app.run_test() as pilot:
        await settle(app, pilot)
        await pilot.press("space", "down", "space", "x")
        await pilot.pause()
        assert len(app._marked) == 2
        assert "2 marked project" in str(app.screen.query_one(".dialog-title", Static).content)
        await pilot.click("#ok")
        await settle(app, pilot)

        assert app._last_result is not None
        assert app._last_result.title == "Batch conform result"
        assert not app._marked
        for name in ("260813_Alpha", "260813_Beta"):
            assert (fixture_drive / name / "11 Meetings" / "kickoff.md").is_file()


async def test_batch_conform_refuses_if_any_preview_becomes_stale(fixture_drive):
    for name in ("260813_Alpha", "260813_Beta"):
        make_project(
            fixture_drive,
            name,
            sections=["01 Model", "Meetings"],
            files={"Meetings/kickoff.md": name},
        )
    app = AtlasApp(fixture_drive)

    async with app.run_test() as pilot:
        await settle(app, pilot)
        await pilot.press("space", "down", "space", "x")
        await pilot.pause()
        (fixture_drive / "260813_Beta" / "CLAUDE.md").write_text("@PROJECT.md\n", encoding="utf-8")
        await pilot.click("#ok")
        await settle(app, pilot)

        assert app._last_result is not None
        assert app._last_result.title == "Batch plan changed"
        assert app._marked == {"260813_Alpha", "260813_Beta"}
        for name in ("260813_Alpha", "260813_Beta"):
            assert (fixture_drive / name / "Meetings" / "kickoff.md").is_file()


async def test_batch_rechecks_each_project_immediately_before_apply(fixture_drive, monkeypatch):
    for name in ("260813_Alpha", "260813_Beta"):
        make_project(
            fixture_drive,
            name,
            sections=["01 Model", "Meetings"],
            files={"Meetings/kickoff.md": name},
        )
    real_apply = tui_app.apply_plan

    def change_later_project(root, project, drive_map, plan):
        result = real_apply(root, project, drive_map, plan)
        if plan.project == "260813_Alpha":
            (fixture_drive / "260813_Beta" / "CLAUDE.md").write_text(
                "@PROJECT.md\n", encoding="utf-8"
            )
        return result

    monkeypatch.setattr(tui_app, "apply_plan", change_later_project)
    app = AtlasApp(fixture_drive)

    async with app.run_test() as pilot:
        await settle(app, pilot)
        await pilot.press("space", "down", "space", "x")
        await pilot.pause()
        await pilot.click("#ok")
        await settle(app, pilot)

        assert app._last_result is not None
        assert app._last_result.title == "Batch conform stopped"
        assert app._marked == {"260813_Beta"}
        assert (fixture_drive / "260813_Alpha" / "11 Meetings" / "kickoff.md").is_file()
        assert (fixture_drive / "260813_Beta" / "Meetings" / "kickoff.md").is_file()


async def test_batch_partial_failure_preserves_progress_and_remaining_mark(fixture_drive, monkeypatch):
    for name in ("260813_Alpha", "260813_Beta"):
        make_project(
            fixture_drive,
            name,
            sections=["01 Model", "Meetings"],
            files={"Meetings/kickoff.md": name},
        )
    real_apply = tui_app.apply_plan

    def fail_second(root, project, drive_map, plan):
        if plan.project == "260813_Beta":
            raise PermissionError("Beta became read-only")
        return real_apply(root, project, drive_map, plan)

    monkeypatch.setattr(tui_app, "apply_plan", fail_second)
    app = AtlasApp(fixture_drive)

    async with app.run_test() as pilot:
        await settle(app, pilot)
        await pilot.press("space", "down", "space", "x")
        await pilot.pause()
        await pilot.click("#ok")
        await settle(app, pilot)

        assert app._last_result is not None
        assert app._last_result.title == "Batch conform stopped"
        assert "Beta became read-only" in "\n".join(app._last_result.lines)
        assert app._marked == {"260813_Beta"}
        assert (fixture_drive / "260813_Alpha" / "11 Meetings" / "kickoff.md").is_file()
        assert (fixture_drive / "260813_Beta" / "Meetings" / "kickoff.md").is_file()


async def test_batch_conflict_remains_marked_for_review(fixture_drive):
    make_project(
        fixture_drive,
        "260813_Conflict",
        sections=["01 Model", "Meetings", "11 Meetings"],
        files={"Meetings/kickoff.md": "source", "11 Meetings/kickoff.md": "target"},
    )
    app = AtlasApp(fixture_drive)

    async with app.run_test() as pilot:
        await settle(app, pilot)
        await pilot.press("space", "x")
        await pilot.pause()
        await pilot.click("#ok")
        await settle(app, pilot)

        assert app._last_result is not None
        assert "1 conflict(s)" in app._last_result.summary
        assert app._marked == {"260813_Conflict"}
        assert (fixture_drive / "260813_Conflict" / "Meetings" / "kickoff.md").is_file()


async def test_single_conform_reports_skipped_actions_as_warning(fixture_drive, monkeypatch):
    make_project(fixture_drive, "260813_Skipped", sections=["01 Model", "Meetings"])

    def skip_all(_root, _project, _drive_map, plan):
        return Plan(
            project=plan.project,
            actions=tuple(
                replace(action, status=SKIPPED, note="changed concurrently")
                for action in plan.actions
            ),
        )

    monkeypatch.setattr(tui_app, "apply_plan", skip_all)
    app = AtlasApp(fixture_drive)

    async with app.run_test() as pilot:
        await settle(app, pilot)
        await pilot.press("f")
        await pilot.pause()
        await pilot.click("#ok")
        await settle(app, pilot)

        assert app._last_result is not None
        assert app._last_result.severity == "warning"
        assert "skipped" in app._last_result.summary


async def test_conform_refuses_when_preview_becomes_stale(fixture_drive):
    make_project(
        fixture_drive,
        "260813_Changed",
        sections=["01 Model", "Meetings"],
        files={"Meetings/kickoff.md": "x"},
    )
    app = AtlasApp(fixture_drive)

    async with app.run_test() as pilot:
        await settle(app, pilot)
        await pilot.press("f")
        await pilot.pause()
        project_md = fixture_drive / "260813_Changed" / "PROJECT.md"
        project_md.write_text("# Human notes\n", encoding="utf-8")
        await pilot.click("#ok")
        await settle(app, pilot)

        assert app._last_result is not None
        assert app._last_result.title == "Conform plan changed"
        assert project_md.read_text(encoding="utf-8") == "# Human notes\n"
        assert (fixture_drive / "260813_Changed" / "Meetings" / "kickoff.md").is_file()
        assert not (fixture_drive / "260813_Changed" / "11 Meetings" / "kickoff.md").exists()
