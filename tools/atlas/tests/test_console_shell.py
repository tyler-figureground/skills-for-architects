"""The console shell as Atlas code (ticket 20, ADR 0005).

Rendered headless at the sizes ticket 03 measured off forty PTY resizes - 179,
153, 120, 87, 77 and 46 columns, 51, 30 and 24 rows - rather than at the 132x38
the effort had been assuming. Single-Region is the common case here, not the
degraded one.
"""

from __future__ import annotations

import asyncio

import pytest
from textual.widgets import Static

from atlas.tui.app import AtlasApp

from conftest import make_project

SPLIT_WIDTHS = (179, 153, 120)
NARROW_WIDTHS = (87, 77, 46)


async def settle(app: AtlasApp, pilot) -> None:
    for _ in range(3):
        await app.workers.wait_for_complete()
        await pilot.pause()


def two_projects(drive):
    make_project(drive, "260501_Alpha", sections=["01 Model", "Meetings"],
                 files={"Meetings/k.md": "z"})
    make_project(drive, "260502_Bravo", sections=["01 Model"])


# ------------------------------------------------------------ Compositions


@pytest.mark.parametrize("width", SPLIT_WIDTHS)
async def test_split_composition_draws_the_list_beside_the_workspace(fixture_drive, width):
    two_projects(fixture_drive)
    app = AtlasApp(fixture_drive, follow_debounce=0)

    async with app.run_test(size=(width, 51)) as pilot:
        await settle(app, pilot)
        assert app.query_one("#projects").display
        assert app.query_one("#workspace").display
        assert app.query_one("#tree").display
        assert app.query_one("#companion").display
        assert not app.query_one("#refusal").display


@pytest.mark.parametrize("width", NARROW_WIDTHS)
async def test_single_region_composition_draws_exactly_one(fixture_drive, width):
    two_projects(fixture_drive)
    app = AtlasApp(fixture_drive, follow_debounce=0)

    async with app.run_test(size=(width, 51)) as pilot:
        await settle(app, pilot)
        assert app.query_one("#projects").display
        assert not app.query_one("#tree").display
        assert not app.query_one("#companion").display

        await pilot.press("tab")
        await pilot.pause()
        assert not app.query_one("#projects").display
        assert app.query_one("#tree").display


async def test_summary_and_operation_merge_at_twenty_four_rows(fixture_drive):
    two_projects(fixture_drive)
    app = AtlasApp(fixture_drive, follow_debounce=0)

    async with app.run_test(size=(120, 24)) as pilot:
        await settle(app, pilot)
        assert not app.query_one("#summary").display
        line = str(app.query_one("#operation", Static).content)
        assert "projects" in line and "ready" in line, line


@pytest.mark.parametrize("size", ((39, 51), (120, 15)))
async def test_too_small_draws_one_honest_line(fixture_drive, size):
    two_projects(fixture_drive)
    app = AtlasApp(fixture_drive, follow_debounce=0)

    async with app.run_test(size=size) as pilot:
        await settle(app, pilot)
        refusal = app.query_one("#refusal", Static)
        assert refusal.display
        assert "40 columns" in str(refusal.content)
        assert not app.query_one("#console").display
        assert not app.query_one("#mark").display
        assert not app.query_one("#operation").display
        assert not app.query_one("#summary").display
        assert not app.query_one("#keys").display


async def test_the_narrow_chrome_names_the_keys_that_move(fixture_drive):
    """46 columns is the single most common measured width. The full binding
    list does not fit and the keys still work - only the chrome shrinks."""
    two_projects(fixture_drive)
    app = AtlasApp(fixture_drive, follow_debounce=0)

    async with app.run_test(size=(46, 51)) as pilot:
        await settle(app, pilot)
        keys = app.query_one("#keys", Static)
        assert keys.display
        assert str(keys.content) == "? Help  Tab Region  Enter Open"
        assert app.check_action("add_section", ()) is True, "still available"


# --------------------------------------------------------------- collapse


async def test_collapse_outranks_the_breakpoint_and_sticks(fixture_drive):
    two_projects(fixture_drive)
    app = AtlasApp(fixture_drive, follow_debounce=0)

    async with app.run_test(size=(179, 51)) as pilot:
        await settle(app, pilot)
        assert app.query_one("#companion").display

        await pilot.press("right_square_bracket")
        await pilot.pause()
        assert not app.query_one("#companion").display, "collapsed at a wide width"

        await pilot.press("left_square_bracket")
        await pilot.pause()
        assert not app.query_one("#projects").display
        assert app.query_one("#tree").display, "focus moved off the collapsed Region"

        await pilot.press("left_square_bracket", "right_square_bracket")
        await pilot.pause()
        assert app.query_one("#projects").display
        assert app.query_one("#companion").display


async def test_zoom_is_single_region_at_any_width(fixture_drive):
    two_projects(fixture_drive)
    app = AtlasApp(fixture_drive, follow_debounce=0)

    async with app.run_test(size=(179, 51)) as pilot:
        await settle(app, pilot)
        await pilot.press("z")
        await pilot.pause()
        assert app.query_one("#projects").display
        assert not app.query_one("#tree").display
        assert not app.query_one("#companion").display

        await pilot.press("escape")
        await pilot.pause()
        assert app.query_one("#tree").display


# -------------------------------------------------------- Companion Modes


async def test_the_companion_shows_real_unmet_expectations(fixture_drive):
    """The default mode is wired to the core seam, not to a placeholder: this is
    what the tree exists to be compared against."""
    make_project(fixture_drive, "260503_Sparse", sections=["01 Model"])
    app = AtlasApp(fixture_drive, follow_debounce=0)

    async with app.run_test(size=(179, 51)) as pilot:
        await settle(app, pilot)
        assert "Unmet expectations" in str(app.query_one("#companion-title", Static).content)
        body = str(app.query_one("#companion-body", Static).content)
        assert "08 OUT" in body, body
        assert "CLAUDE.md" in body, body
        assert "(add folders)" in body, "a section is not a Backfill"


async def test_d_cycles_the_modes_and_a_new_project_snaps_back(fixture_drive):
    two_projects(fixture_drive)
    app = AtlasApp(fixture_drive, follow_debounce=0)

    async with app.run_test(size=(179, 51)) as pilot:
        await settle(app, pilot)
        await pilot.press("d")
        await pilot.pause()
        assert "Project health" in str(app.query_one("#companion-title", Static).content)

        await pilot.press("d")
        await pilot.pause()
        assert "Dossier" in str(app.query_one("#companion-title", Static).content)

        await pilot.press("down")
        await pilot.pause()
        assert "Unmet expectations" in str(app.query_one("#companion-title", Static).content)


async def test_the_workspace_title_carries_the_project_name(fixture_drive):
    two_projects(fixture_drive)
    app = AtlasApp(fixture_drive, follow_debounce=0)

    async with app.run_test(size=(179, 51)) as pilot:
        await settle(app, pilot)
        assert str(app.query_one("#workspace-title", Static).content) == "260501_Alpha"
        await pilot.press("down")
        await pilot.pause()
        assert str(app.query_one("#workspace-title", Static).content) == "260502_Bravo"


# ------------------------------------------------------------ cursor follow


async def test_the_workspace_waits_out_a_moving_cursor_but_not_a_cached_one(fixture_drive):
    """Debounced so that holding a key down does not enumerate every project it
    passes over; exempt on a cache hit, because there is nothing to wait for."""
    # The two must differ in what the map expects of them, or "did the Companion
    # update" is unanswerable.
    make_project(fixture_drive, "260501_Alpha", sections=["01 Model"])
    make_project(fixture_drive, "260502_Bravo",
                 sections=["01 Model/01 Site Model", "01 Model/02 Design",
                           "06 Research/Zoning", "06 Research/Code", "08 OUT",
                           "10 Legal", "11 Meetings"],
                 files={"CLAUDE.md": "x"})
    app = AtlasApp(fixture_drive, follow_debounce=0.5)

    async with app.run_test(size=(179, 51)) as pilot:
        await settle(app, pilot)
        await asyncio.sleep(0.6)
        await pilot.pause()
        first = str(app.query_one("#companion-body", Static).content)

        await pilot.press("down")
        await pilot.pause()
        assert str(app.query_one("#companion-body", Static).content) == first, "still pending"
        await asyncio.sleep(0.6)
        await pilot.pause()
        second = str(app.query_one("#companion-body", Static).content)
        assert second != first

        await pilot.press("up")
        await pilot.pause()
        assert str(app.query_one("#companion-body", Static).content) == first, "cache hit"


async def test_the_palette_switches_the_companion_instead_of_pushing_a_modal(fixture_drive):
    """The command that used to open a project-health modal now switches a
    Companion Mode. It is also the one place a deleted action would have gone
    unnoticed: the palette only builds its entries when Atlas is not busy."""
    two_projects(fixture_drive)
    app = AtlasApp(fixture_drive, follow_debounce=0)

    async with app.run_test(size=(179, 51)) as pilot:
        await settle(app, pilot)
        commands = {command.title for command in app.get_system_commands(app.screen)}
        assert "Project health" in commands

        app.action_show_health()
        await pilot.pause()
        assert app.screen is app.screen_stack[0], "no modal"
        assert "Project health" in str(app.query_one("#companion-title", Static).content)
        assert "ATLAS CAN FIX" in str(app.query_one("#companion-body", Static).content)


async def test_a_cursor_passing_through_never_enumerates_what_it_passed(fixture_drive):
    """The cancellation path. Holding the cursor key down walks the list; only
    where it comes to rest is worth an enumeration."""
    make_project(fixture_drive, "260504_One", sections=["01 Model"])
    make_project(fixture_drive, "260505_Two", sections=["01 Model", "06 Research"])
    make_project(fixture_drive, "260506_Three",
                 sections=["01 Model", "06 Research", "08 OUT", "10 Legal"])
    app = AtlasApp(fixture_drive, follow_debounce=0.5)

    async with app.run_test(size=(179, 51)) as pilot:
        await settle(app, pilot)
        await asyncio.sleep(0.6)
        await pilot.pause()

        await pilot.press("down")
        await pilot.press("down")
        await pilot.pause()
        assert app._workspace_project == "260506_Three"
        # Passed straight over the middle project, so it was never opened.
        assert "260505_Two" not in app._trees

        await asyncio.sleep(0.6)
        await pilot.pause()
        assert "260506_Three" in app._trees
        assert "260505_Two" not in app._trees
