"""TUI pilot smoke tests - the wizards drive the same core the CLI uses, so
these verify wiring, not logic (logic is covered in test_ops/test_conform)."""

from __future__ import annotations

from datetime import date

from atlas.core.mapfile import find_map, load_map
from atlas.core.ops import new_project
from atlas.tui.app import AtlasApp, NewProjectModal

from conftest import make_project


async def test_tui_boots_and_lists_projects(fixture_drive):
    m = load_map(find_map(fixture_drive))
    new_project(fixture_drive, m, "Alpha", created=date(2026, 8, 13))
    make_project(fixture_drive, "260813_Beta", sections=["01 Model"])

    app = AtlasApp(fixture_drive)
    async with app.run_test() as pilot:
        await pilot.pause()
        table = app.query_one("#projects")
        assert table.row_count == 2
        assert "TESTDRIVE" in app.sub_title


async def test_new_project_wizard_creates_on_disk(fixture_drive):
    app = AtlasApp(fixture_drive)
    async with app.run_test() as pilot:
        await pilot.pause()
        await pilot.press("n")
        await pilot.pause()
        assert isinstance(app.screen, NewProjectModal)
        app.screen.query_one("#name").value = "Wizard House"
        app.screen.query_one("#desc").value = "ADU"
        await pilot.pause()
        await pilot.click("#ok")
        await pilot.pause()

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
        await pilot.pause()
        await pilot.press("f")
        await pilot.pause()
        await pilot.click("#ok")
        await pilot.pause()

    project = fixture_drive / "260813_Fixit"
    assert (project / "11 Meetings" / "kickoff.md").is_file()
    assert (project / "PROJECT.md").is_file()
