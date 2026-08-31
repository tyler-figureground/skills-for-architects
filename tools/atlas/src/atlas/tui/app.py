"""Atlas operations console - thin, safe views over the core modules.

The TUI owns interaction state, background work, and durable feedback. Filesystem
rules stay in ``atlas.core`` so CLI and TUI mutations follow the same plan and
safety contracts.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass
from datetime import date
import os
from pathlib import Path

from rich.text import Text
from textual import work
from textual.app import App, ComposeResult, SystemCommand
from textual.binding import Binding
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.screen import ModalScreen, Screen
from textual.widgets import (
    Button,
    DataTable,
    Footer,
    Header,
    Input,
    Label,
    ListItem,
    ListView,
    SelectionList,
    Static,
)

from ..core.conform import CONFLICT, DONE, SKIPPED, Plan, apply_plan, build_plan
from ..core.doctor import DriveReport, report_project
from ..core.mapfile import DriveMap
from ..core.naming import build_folder_name, clean_name_part
from ..core.ops import OpsError, add_sections, find_empty_dirs, new_project, remove_empty_dirs
from ..core.scan import DriveInventory, ProjectInventory, discover_drives, scan_drive
from .model import ProjectRow, project_detail, project_rows, visible_rows

STATUS_STYLES = {
    "READY": "bold green",
    "ACTION": "bold yellow",
    "REVIEW": "bold red",
    "SETUP": "bold cyan",
}

MODAL_CSS = """
ModalScreen { align: center middle; }
#dialog {
    width: 76; max-width: 94%; max-height: 88%; padding: 1 2;
    background: $surface; border: thick $primary;
}
#dialog .dialog-title { text-style: bold; margin-bottom: 1; }
#dialog .field-label { color: $text-muted; }
#dialog Input { margin-bottom: 1; }
#dialog SelectionList { max-height: 18; margin-bottom: 1; }
#dialog.selection-dialog { height: 80%; min-height: 12; }
#dialog.selection-dialog SelectionList { height: 1fr; max-height: 1fr; }
#dialog #plan { max-height: 22; margin-bottom: 1; }
#dialog .actions { height: 3; align-horizontal: right; }
#dialog Button { margin-left: 2; }
#dialog #preview, #dialog .supporting { color: $text-muted; margin-bottom: 1; }
"""


def _project_token(project: ProjectInventory) -> tuple[tuple[str, bool], ...]:
    """Shallow project state reviewed by plans without hydrating remote file contents."""

    return tuple(sorted((entry.name, entry.is_dir) for entry in project.root_entries))


@dataclass(frozen=True)
class OperationOutcome:
    """Durable summary and inspectable detail from one filesystem operation."""

    title: str
    summary: str
    lines: tuple[str, ...]
    severity: str = "information"
    marks_after: tuple[str, ...] | None = None


class NewProjectModal(ModalScreen[tuple[str, str] | None]):
    """Collect a project name and show the exact stamped folder name."""

    BINDINGS = [Binding("escape", "cancel", "Cancel", show=False)]

    def compose(self) -> ComposeResult:
        with Vertical(id="dialog"):
            yield Label("New project", classes="dialog-title")
            yield Label("Project name or address", classes="field-label")
            yield Input(placeholder="Example: 1842 Oak Street", id="name")
            yield Label("Descriptor (optional)", classes="field-label")
            yield Input(placeholder="Example: ADU or Renovation", id="desc")
            yield Static("", id="preview", markup=False)
            with Horizontal(classes="actions"):
                yield Button("Create project", variant="primary", id="ok", disabled=True)
                yield Button("Cancel", id="cancel")

    def on_mount(self) -> None:
        self._sync_preview()
        self.query_one("#name", Input).focus()

    def on_input_changed(self, _: Input.Changed) -> None:
        self._sync_preview()

    def on_input_submitted(self, _: Input.Submitted) -> None:
        if not self.query_one("#ok", Button).disabled:
            self._submit()

    def _sync_preview(self) -> None:
        name = clean_name_part(self.query_one("#name", Input).value)
        desc = clean_name_part(self.query_one("#desc", Input).value)
        preview = build_folder_name(date.today(), name or "<project name>", desc)
        self.query_one("#preview", Static).update(f"Folder name: {preview}")
        self.query_one("#ok", Button).disabled = not bool(name)

    def _submit(self) -> None:
        self.dismiss(
            (
                self.query_one("#name", Input).value,
                self.query_one("#desc", Input).value,
            )
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "ok":
            self._submit()
        else:
            self.action_cancel()

    def action_cancel(self) -> None:
        self.dismiss(None)


class AddSectionModal(ModalScreen[list[str] | None]):
    """Choose map-approved folders that do not exist yet."""

    BINDINGS = [Binding("escape", "cancel", "Cancel", show=False)]

    def __init__(self, project: str, options: list[str]) -> None:
        super().__init__()
        self._project = project
        self._options = options

    def compose(self) -> ComposeResult:
        with Vertical(id="dialog", classes="selection-dialog"):
            yield Label(f"Add folders - {self._project}", classes="dialog-title")
            yield Static(
                "Only folders approved by the drive map appear here.",
                classes="supporting",
                markup=False,
            )
            yield SelectionList[str](
                *[(self._option_label(option), option) for option in self._options]
            )
            with Horizontal(classes="actions"):
                yield Button("Create selected", variant="primary", id="ok", disabled=True)
                yield Button("Cancel", id="cancel")

    def on_mount(self) -> None:
        self.query_one(SelectionList).focus()

    @staticmethod
    def _option_label(option: str) -> str:
        if "/" not in option:
            return f"{option}  (section)"
        section, child = option.split("/", 1)
        return f"  {section} / {child}"

    def on_selection_list_selected_changed(self, _: SelectionList.SelectedChanged) -> None:
        selected = self.query_one(SelectionList).selected
        self.query_one("#ok", Button).disabled = not bool(selected)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "ok":
            self.dismiss(list(self.query_one(SelectionList).selected))
        else:
            self.action_cancel()

    def action_cancel(self) -> None:
        self.dismiss(None)


class ConfirmListModal(ModalScreen[bool]):
    """Show an exact plan before a filesystem mutation."""

    BINDINGS = [Binding("escape", "cancel", "Cancel", show=False)]

    def __init__(self, title: str, lines: list[str], ok_label: str) -> None:
        super().__init__()
        self._title = title
        self._lines = lines
        self._ok = ok_label

    def compose(self) -> ComposeResult:
        with Vertical(id="dialog"):
            yield Label(self._title, classes="dialog-title")
            yield Static(
                "Move destinations are never replaced. Concurrent control-file changes stop the plan.",
                classes="supporting",
                markup=False,
            )
            with VerticalScroll(id="plan"):
                yield Static("\n".join(self._lines) or "Nothing to do.", markup=False)
            with Horizontal(classes="actions"):
                if self._lines:
                    yield Button(self._ok, variant="warning", id="ok")
                yield Button("Close", id="cancel")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.dismiss(event.button.id == "ok")

    def action_cancel(self) -> None:
        self.dismiss(False)


class ResultModal(ModalScreen[None]):
    """Persistent, copyable operation or project detail."""

    BINDINGS = [Binding("escape", "close", "Close", show=False)]

    def __init__(self, title: str, lines: Iterable[str]) -> None:
        super().__init__()
        self._title = title
        self._lines = tuple(lines)

    def compose(self) -> ComposeResult:
        with Vertical(id="dialog"):
            yield Label(self._title, classes="dialog-title")
            with VerticalScroll(id="plan"):
                yield Static("\n".join(self._lines), markup=False)
            with Horizontal(classes="actions"):
                yield Button("Close", variant="primary", id="cancel")

    def on_button_pressed(self, _: Button.Pressed) -> None:
        self.action_close()

    def action_close(self) -> None:
        self.dismiss(None)


class AtlasApp(App):
    TITLE = "Atlas"
    HORIZONTAL_BREAKPOINTS = [(0, "-narrow"), (100, "-wide")]
    CSS = MODAL_CSS + """
    Screen { layout: vertical; }
    #drives { height: 1fr; padding: 1 2; }
    #filter { display: none; margin: 0 1; }
    #workspace { height: 1fr; }
    #projects { width: 3fr; height: 1fr; }
    #detail {
        width: 2fr; min-width: 36; height: 1fr; padding: 1 2;
        border-left: solid $primary-background;
    }
    #detail-title { height: auto; text-style: bold; margin-bottom: 1; }
    #detail-body { height: auto; }
    Screen.-narrow #detail { display: none; }
    #summary { height: 1; padding: 0 2; color: $text-muted; }
    #operation { height: 1; padding: 0 2; background: $boost; }
    #operation.-warning { color: $warning; }
    #operation.-error { color: $error; }
    Footer { dock: bottom; }
    """
    BINDINGS = [
        Binding("q", "quit", "Quit", show=False),
        Binding("r", "refresh", "Refresh", show=False),
        Binding("slash", "filter_projects", "Filter"),
        Binding("enter", "inspect", "Inspect"),
        Binding("n", "new_project", "New", show=False),
        Binding("a", "add_section", "Add folders"),
        Binding("c", "clean", "Clean", show=False),
        Binding("f", "conform", "Conform"),
        Binding("o", "open_folder", "Open", show=False),
        Binding("space", "toggle_mark", "Mark", show=False),
        Binding("x", "conform_marked", "Conform marked", show=False),
        Binding("s", "cycle_sort", "Sort", show=False),
        Binding("l", "show_last_result", "Last result", show=False),
        Binding("question_mark", "show_help_panel", "Help"),
        Binding("escape", "back", "Back", show=False),
    ]

    def __init__(self, drive: Path | None = None) -> None:
        super().__init__()
        self._initial_drive = drive
        self._drives: list[Path] = []
        self._inventory: DriveInventory | None = None
        self._rows: tuple[ProjectRow, ...] = ()
        self._visible_rows: tuple[ProjectRow, ...] = ()
        self._marked: set[str] = set()
        self._sort_column = "health"
        self._sort_reverse = False
        self._busy = False
        self._work_kind: str | None = None
        self._inventory_fresh = False
        self._scan_generation = 0
        self._announced_scan_generation = 0
        self._last_result: OperationOutcome | None = None

    # ------------------------------------------------------------- lifecycle

    def compose(self) -> ComposeResult:
        yield Header()
        yield ListView(id="drives")
        yield Input(placeholder="Filter by project name or health", id="filter")
        with Horizontal(id="workspace"):
            yield DataTable(id="projects")
            with VerticalScroll(id="detail"):
                yield Static("Project health", id="detail-title", markup=False)
                yield Static("Select a project to inspect it.", id="detail-body", markup=False)
        yield Static("", id="summary", markup=False)
        yield Static("Ready", id="operation", markup=False)
        yield Footer()

    def on_mount(self) -> None:
        table = self.query_one("#projects", DataTable)
        table.add_column("Mark", key="mark", width=4)
        table.add_column("Health", key="health")
        table.add_column("Project", key="project")
        table.add_column("Sections", key="sections")
        table.add_column("Fixes", key="fixes")
        table.add_column("Review", key="review")
        table.cursor_type = "row"
        table.display = False
        self.query_one("#workspace", Horizontal).display = False
        if self._initial_drive:
            self._open_drive(self._initial_drive)
        else:
            self._show_drives(auto_open=True)

    # ------------------------------------------------------------- commands

    def get_system_commands(self, screen: Screen) -> Iterable[SystemCommand]:
        yield from super().get_system_commands(screen)
        if screen is not self.screen_stack[0] or self._busy:
            return
        if self._inventory is not None:
            yield SystemCommand("Filter projects", "Find a project or health state", self.action_filter_projects)
            yield SystemCommand("Refresh drive", "Rescan project health", self.action_refresh)
            if self._inventory_fresh:
                yield SystemCommand("New project", "Create a mapped project", self.action_new_project)
        if self._selected_row() is not None:
            yield SystemCommand("Inspect project", "Show exact findings", self.action_inspect)
            yield SystemCommand("Open project folder", "Open in the default file manager", self.action_open_folder)
            yield SystemCommand("Mark or unmark project", "Build a batch selection", self.action_toggle_mark)
            if self._inventory_fresh:
                yield SystemCommand("Add project folders", "Create map-approved folders", self.action_add_section)
                yield SystemCommand("Clean empty folders", "Preview removable empty folders", self.action_clean)
                yield SystemCommand("Conform project", "Preview mapped repairs", self.action_conform)
        if self._marked and self._inventory_fresh:
            yield SystemCommand(
                "Conform marked projects",
                f"Preview repairs for {len(self._marked)} marked project(s)",
                self.action_conform_marked,
            )
        if self._last_result is not None:
            yield SystemCommand("Show last result", "Review the latest operation", self.action_show_last_result)

    def check_action(self, action: str, parameters: tuple[object, ...]) -> bool | None:
        has_drive = self._inventory is not None
        has_project = self._selected_row() is not None
        if action == "refresh":
            return True if not self._busy else None
        if action in {"filter_projects", "cycle_sort"}:
            return True if has_drive and not self._busy else None
        if action == "new_project":
            return True if has_drive and self._inventory_fresh and not self._busy else None
        if action in {"add_section", "clean", "conform"}:
            return True if has_project and self._inventory_fresh and not self._busy else None
        if action == "conform_marked":
            return True if self._marked and self._inventory_fresh and not self._busy else None
        if action in {"inspect", "open_folder", "toggle_mark"}:
            return True if has_project and not self._busy else None
        if action == "show_last_result":
            return True if self._last_result is not None else False
        return super().check_action(action, parameters)

    # ------------------------------------------------------------- drives and scans

    def _show_drives(self, *, auto_open: bool) -> None:
        self._scan_generation += 1
        self._busy = False
        self._work_kind = None
        self._inventory_fresh = False
        self._inventory = None
        self._rows = ()
        self._visible_rows = ()
        self._marked.clear()
        self.sub_title = "Drive picker"
        try:
            self._drives = discover_drives()
        except OSError as error:
            self._drives = []
            self._set_operation(f"Drive discovery failed: {error}. Press r to retry.", "error")
        drive_list = self.query_one("#drives", ListView)
        drive_list.clear()
        for drive in self._drives:
            drive_list.append(ListItem(Static(str(drive), markup=False)))
        drive_list.display = True
        self.query_one("#workspace", Horizontal).display = False
        self.query_one("#filter", Input).display = False
        self.query_one("#summary", Static).update(
            f"{len(self._drives)} mapped drive(s) - Enter to open"
            if self._drives
            else "No mapped drives - set ATLAS_MOUNT_ROOT or launch with --drive"
        )
        if auto_open and len(self._drives) == 1:
            self._open_drive(self._drives[0])
        else:
            drive_list.focus()
        self.refresh_bindings()

    def on_list_view_selected(self, _: ListView.Selected) -> None:
        index = self.query_one("#drives", ListView).index
        if index is not None and 0 <= index < len(self._drives):
            self._open_drive(self._drives[index])

    def _open_drive(self, root: Path, *, announce: bool = True) -> None:
        self._busy = True
        self._work_kind = "scan"
        self._inventory_fresh = False
        self._scan_generation += 1
        generation = self._scan_generation
        table = self.query_one("#projects", DataTable)
        table.loading = True
        if announce:
            self._announced_scan_generation = generation
            self._set_operation(f"Scanning {root.name}...")
        self.refresh_bindings()
        self._scan_drive_worker(root, generation)

    @work(thread=True, exclusive=True, group="scan", exit_on_error=False)
    def _scan_drive_worker(self, root: Path, generation: int) -> None:
        try:
            inventory = scan_drive(root)
            report = DriveReport(
                root=inventory.root,
                drive=inventory.map.drive,
                map_version=inventory.map.version,
                projects=tuple(
                    report_project(project, inventory.map) for project in inventory.projects
                ),
            )
            rows = project_rows(report.projects, inventory.map)
        except Exception as error:  # filesystem, map, permissions, disconnected drive
            self.call_from_thread(self._scan_failed, generation, root, error)
            return
        self.call_from_thread(self._scan_succeeded, generation, inventory, report, rows)

    def _scan_succeeded(
        self,
        generation: int,
        inventory: DriveInventory,
        report: DriveReport,
        rows: tuple[ProjectRow, ...],
    ) -> None:
        if generation != self._scan_generation:
            return
        self._inventory = inventory
        self._rows = rows
        current_names = {row.key for row in rows}
        self._marked.intersection_update(current_names)
        self._busy = False
        self._work_kind = None
        self._inventory_fresh = True
        table = self.query_one("#projects", DataTable)
        table.loading = False
        table.display = True
        self.query_one("#drives", ListView).display = False
        self.query_one("#workspace", Horizontal).display = True
        self.sub_title = f"{report.drive} - map v{report.map_version}"
        self._fill()
        if generation == self._announced_scan_generation:
            self._set_operation(f"Scan complete - {len(self._rows)} project(s)")
        table.focus()
        self.refresh_bindings()

    def _scan_failed(self, generation: int, root: Path, error: Exception) -> None:
        if generation != self._scan_generation:
            return
        self._busy = False
        self._work_kind = None
        self.query_one("#projects", DataTable).loading = False
        message = f"Could not scan {root.name}: {error}. Press r to retry."
        self._set_operation(message, "error")
        self.notify(message, title="Scan failed", severity="error", timeout=10)
        self.refresh_bindings()

    # ------------------------------------------------------------- table and detail

    def _fill(self, preserve: str | None = None) -> None:
        if self._inventory is None:
            return
        selected = preserve or (self._selected_row().key if self._selected_row() else None)
        query = self.query_one("#filter", Input).value
        self._visible_rows = visible_rows(
            self._rows,
            query=query,
            sort_column=self._sort_column,
            reverse=self._sort_reverse,
        )
        table = self.query_one("#projects", DataTable)
        table.clear()
        for row in self._visible_rows:
            table.add_row(
                "*" if row.key in self._marked else "",
                Text(row.health, style=STATUS_STYLES.get(row.health, "bold")),
                row.report.name,
                row.sections,
                str(row.fixes) if row.fixes else "-",
                str(row.review) if row.review else "-",
                key=row.key,
            )

        if self._visible_rows:
            selected_index = next(
                (index for index, row in enumerate(self._visible_rows) if row.key == selected),
                0,
            )
            table.move_cursor(row=selected_index)
            self._update_detail(self._visible_rows[selected_index])
        else:
            self.query_one("#detail-title", Static).update("No matching projects")
            self.query_one("#detail-body", Static).update(
                "Change the filter or press Esc to show every project."
                if query
                else "No project folders found on this drive. Press n to create one."
            )

        counts = DriveReport(
            root=self._inventory.root,
            drive=self._inventory.map.drive,
            map_version=self._inventory.map.version,
            projects=tuple(row.report for row in self._rows),
        ).summary()
        direction = "desc" if self._sort_reverse else "asc"
        filter_note = f" | Filter: {query}" if query else ""
        self.query_one("#summary", Static).update(
            f"{len(self._rows)} projects | {counts['conform']} ready | "
            f"{counts['drift']} action | {counts['unfiled']} review | "
            f"{counts['stub']} setup | {len(self._marked)} marked | "
            f"{self._sort_column} {direction}{filter_note}"
        )
        self.refresh_bindings()

    def _selected_row(self) -> ProjectRow | None:
        if not self._visible_rows:
            return None
        cursor_row = self.query_one("#projects", DataTable).cursor_row
        if cursor_row is None or cursor_row >= len(self._visible_rows):
            return None
        return self._visible_rows[cursor_row]

    def _selected_project(self) -> tuple[Path, str] | None:
        row = self._selected_row()
        if row is None or self._inventory is None:
            return None
        return self._inventory.root / row.key, row.key

    def _update_detail(self, row: ProjectRow) -> None:
        self.query_one("#detail-title", Static).update(row.key)
        self.query_one("#detail-body", Static).update(project_detail(row))

    def on_data_table_row_highlighted(self, event: DataTable.RowHighlighted) -> None:
        name = str(event.row_key.value)
        row = next((candidate for candidate in self._visible_rows if candidate.key == name), None)
        if row is not None:
            self._update_detail(row)
            self.refresh_bindings()

    def on_data_table_row_selected(self, _: DataTable.RowSelected) -> None:
        self.action_inspect()

    def on_data_table_header_selected(self, event: DataTable.HeaderSelected) -> None:
        column = str(event.column_key.value)
        if column not in {"health", "project", "sections", "fixes", "review"}:
            return
        selected = self._selected_row()
        preserve = selected.key if selected else None
        if column == self._sort_column:
            self._sort_reverse = not self._sort_reverse
        else:
            self._sort_column = column
            self._sort_reverse = column in {"sections", "fixes", "review"}
        self._fill(preserve)

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id == "filter":
            self._fill()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "filter":
            self.query_one("#projects", DataTable).focus()

    # ------------------------------------------------------------- feedback and workers

    def _set_operation(self, message: str, severity: str = "information") -> None:
        status = self.query_one("#operation", Static)
        status.remove_class("-warning", "-error")
        if severity in {"warning", "error"}:
            status.add_class(f"-{severity}")
        status.update(message)

    def _start_operation(
        self,
        label: str,
        root: Path,
        operation: Callable[[], OperationOutcome],
    ) -> None:
        if self._busy or not self._inventory_fresh:
            return
        self._busy = True
        self._work_kind = "operation"
        self._set_operation(f"{label}...")
        self.refresh_bindings()
        self._operation_worker(root, operation)

    @work(thread=True, exclusive=True, group="operation", exit_on_error=False)
    def _operation_worker(
        self,
        root: Path,
        operation: Callable[[], OperationOutcome],
    ) -> None:
        try:
            outcome = operation()
        except Exception as error:  # core errors plus filesystem/permission failures
            outcome = OperationOutcome(
                title="Operation stopped",
                summary=f"Operation stopped: {error}",
                lines=(
                    str(error),
                    "Some changes may have completed before the failure.",
                    "Atlas will rescan the project. Review current health before retrying.",
                ),
                severity="error",
            )
        self.call_from_thread(self._operation_finished, root, outcome)

    def _operation_finished(self, root: Path, outcome: OperationOutcome) -> None:
        self._busy = False
        self._work_kind = None
        self._last_result = outcome
        if outcome.marks_after is not None:
            self._marked = set(outcome.marks_after)
        self._set_operation(f"Last result: {outcome.summary} - press l for details", outcome.severity)
        self.notify(
            outcome.summary,
            title=outcome.title,
            severity=outcome.severity,
            timeout=10 if outcome.severity != "information" else 5,
        )
        if outcome.severity in {"warning", "error"}:
            self.push_screen(ResultModal(outcome.title, outcome.lines))
        self._open_drive(root, announce=False)

    def _preparation_failed(self, label: str, error: Exception) -> None:
        self._busy = False
        self._work_kind = None
        message = f"Could not {label}: {error}. Review access and retry."
        self._set_operation(message, "error")
        self.notify(message, title="Preparation failed", severity="error", timeout=10)
        self.refresh_bindings()

    # ------------------------------------------------------------- actions

    def action_refresh(self) -> None:
        if self._busy:
            return
        if self._inventory is not None:
            self._open_drive(self._inventory.root)
        elif self._initial_drive:
            self._open_drive(self._initial_drive)
        else:
            self._show_drives(auto_open=False)

    def action_back(self) -> None:
        if self._busy and self._work_kind != "scan":
            self.notify("Wait for the current operation to finish", title="Atlas is working")
            return
        if self._work_kind == "scan":
            self._show_drives(auto_open=False)
            return
        filter_input = self.query_one("#filter", Input)
        if filter_input.display:
            filter_input.value = ""
            filter_input.display = False
            self.query_one("#projects", DataTable).focus()
            return
        if self._inventory is not None:
            self._show_drives(auto_open=False)

    def action_filter_projects(self) -> None:
        if self._busy or self._inventory is None:
            return
        filter_input = self.query_one("#filter", Input)
        filter_input.display = True
        filter_input.focus()

    def action_cycle_sort(self) -> None:
        if self._busy or self._inventory is None:
            return
        columns = ("health", "project", "fixes", "review")
        selected = self._selected_row()
        preserve = selected.key if selected else None
        index = (columns.index(self._sort_column) + 1) % len(columns) if self._sort_column in columns else 0
        self._sort_column = columns[index]
        self._sort_reverse = self._sort_column in {"fixes", "review"}
        self._fill(preserve)

    def action_toggle_mark(self) -> None:
        if self._busy:
            return
        row = self._selected_row()
        if row is None:
            return
        if row.key in self._marked:
            self._marked.remove(row.key)
        else:
            self._marked.add(row.key)
        self._fill(row.key)

    def action_conform_marked(self) -> None:
        if self._busy or not self._inventory_fresh or self._inventory is None or not self._marked:
            return
        inventory = self._inventory
        root = inventory.root
        drive_map = inventory.map
        rows_by_name = {row.key: row for row in self._rows}
        names = sorted(name for name in self._marked if name in rows_by_name)
        plans: dict[str, Plan] = {
            name: build_plan(rows_by_name[name].report, drive_map) for name in names
        }
        inventory_projects = {project.name: project for project in inventory.projects}
        initial_tokens = {name: _project_token(inventory_projects[name]) for name in names}
        lines: list[str] = []
        for name in names:
            plan = plans[name]
            lines.append(name)
            if plan.empty:
                lines.append("  No mapped repairs pending")
            for action in plan.actions:
                source = f"{action.src} -> " if action.src else ""
                files = f" ({action.file_count} files)" if action.file_count else ""
                lines.append(f"  {action.kind.title()}: {source}{action.dst}{files}")

        def done(confirmed: bool) -> None:
            if not confirmed:
                return

            def conform_batch() -> OperationOutcome:
                fresh_inventory = scan_drive(root)
                fresh_map = fresh_inventory.map
                fresh_projects = {project.name: project for project in fresh_inventory.projects}
                fresh_plans: dict[str, Plan] = {}
                fresh_tokens: dict[str, tuple[tuple[str, bool], ...]] = {}
                changed: list[str] = []
                for name in names:
                    project = fresh_projects.get(name)
                    if project is None:
                        changed.append(f"{name}: project no longer available")
                        continue
                    fresh_plan = build_plan(report_project(project, fresh_map), fresh_map)
                    fresh_plans[name] = fresh_plan
                    fresh_tokens[name] = _project_token(project)
                    if (
                        fresh_plan.actions != plans[name].actions
                        or fresh_tokens[name] != initial_tokens[name]
                    ):
                        changed.append(f"{name}: project contents changed")
                if fresh_map != drive_map:
                    changed.insert(0, "Drive map changed")
                if changed:
                    return OperationOutcome(
                        title="Batch plan changed",
                        summary="Marked projects changed since preview - nothing moved",
                        lines=tuple(changed) + ("Run Conform marked again to review current plans.",),
                        severity="warning",
                        marks_after=tuple(names),
                    )

                detail: list[str] = []
                done_count = 0
                skipped = 0
                conflicts = 0
                ready = 0
                completed = 0
                unresolved: set[str] = set()
                for index, name in enumerate(names):
                    immediate_inventory = scan_drive(root)
                    immediate_projects = {
                        project.name: project for project in immediate_inventory.projects
                    }
                    immediate_project = immediate_projects.get(name)
                    immediate_plan = (
                        build_plan(report_project(immediate_project, immediate_inventory.map), immediate_inventory.map)
                        if immediate_project is not None
                        else None
                    )
                    immediate_token = (
                        _project_token(immediate_project) if immediate_project is not None else None
                    )
                    if (
                        immediate_inventory.map != fresh_map
                        or immediate_plan != fresh_plans[name]
                        or immediate_token != fresh_tokens[name]
                    ):
                        detail.extend((name, "  STOPPED: project or drive map changed"))
                        remaining = unresolved | set(names[index:])
                        return OperationOutcome(
                            title="Batch conform stopped",
                            summary=f"Batch stopped after {completed} project(s) - review remaining marks",
                            lines=tuple(detail),
                            severity="warning",
                            marks_after=tuple(sorted(remaining)),
                        )

                    project_path = root / name
                    try:
                        result = apply_plan(root, project_path, immediate_inventory.map, immediate_plan)
                    except Exception as error:
                        detail.extend(
                            (
                                name,
                                f"  FAILED: {error}",
                                "  Some changes may have completed in this project.",
                            )
                        )
                        remaining = unresolved | set(names[index:])
                        return OperationOutcome(
                            title="Batch conform stopped",
                            summary=f"Batch failed after {completed} project(s) - review remaining marks",
                            lines=tuple(detail),
                            severity="error",
                            marks_after=tuple(sorted(remaining)),
                        )

                    completed += 1
                    detail.append(name)
                    if result.empty:
                        ready += 1
                        detail.append("  READY: no mapped repairs pending")
                    project_unresolved = False
                    for action in result.actions:
                        source = f"{action.src} -> " if action.src else ""
                        note = f" - {action.note}" if action.note else ""
                        detail.append(
                            f"  {(action.status or 'planned').upper()}: "
                            f"{action.kind} {source}{action.dst}{note}"
                        )
                        done_count += int(action.status == DONE)
                        skipped += int(action.status == SKIPPED)
                        conflicts += int(action.status == CONFLICT)
                        project_unresolved |= action.status != DONE
                    if project_unresolved:
                        unresolved.add(name)

                severity = "warning" if unresolved else "information"
                summary = (
                    f"Batch complete: {completed} project(s), {done_count} done, "
                    f"{skipped} skipped, {conflicts} conflict(s), {ready} already ready"
                )
                return OperationOutcome(
                    title="Batch conform result",
                    summary=summary,
                    lines=tuple(detail),
                    severity=severity,
                    marks_after=tuple(sorted(unresolved)),
                )

            self._start_operation("Conforming marked projects", root, conform_batch)

        total_repairs = sum(len(plan.actions) for plan in plans.values())
        if total_repairs == 0:
            self._set_operation("Marked projects have no mapped repairs pending")
            self.notify("Marked projects are already ready", title="Nothing to conform")
            return
        self.push_screen(
            ConfirmListModal(
                f"Conform {len(names)} marked project(s)",
                lines,
                f"Apply {total_repairs} repair(s) across {len(names)} project(s)",
            ),
            done,
        )

    def action_inspect(self) -> None:
        if self._busy:
            return
        row = self._selected_row()
        if row is not None:
            self.push_screen(ResultModal(f"Project health - {row.key}", project_detail(row).splitlines()))

    def action_show_last_result(self) -> None:
        if self._last_result is not None:
            self.push_screen(ResultModal(self._last_result.title, self._last_result.lines))

    def action_open_folder(self) -> None:
        if self._busy:
            return
        selected = self._selected_project()
        if selected is None:
            return
        project_path, name = selected
        try:
            if not hasattr(os, "startfile"):
                raise OSError("default folder opening is available on Windows only")
            os.startfile(project_path)  # type: ignore[attr-defined]
        except OSError as error:
            self._set_operation(f"Could not open {name}: {error}", "error")
            self.notify(str(error), title="Open folder failed", severity="error", timeout=10)
            return
        self._set_operation(f"Opened {name} in the default file manager")

    def action_new_project(self) -> None:
        if self._busy or not self._inventory_fresh or self._inventory is None:
            return

        def done(result: tuple[str, str] | None) -> None:
            if not result or self._inventory is None:
                return
            root = self._inventory.root
            drive_map = self._inventory.map

            def create() -> OperationOutcome:
                fresh_map = scan_drive(root).map
                if fresh_map != drive_map:
                    return OperationOutcome(
                        title="Project plan changed",
                        summary="Drive map changed - no project created",
                        lines=("Open New project again to review the current folder rules.",),
                        severity="warning",
                    )
                created = new_project(root, fresh_map, result[0], result[1])
                return OperationOutcome(
                    title="Project created",
                    summary=f"Created {created.folder_name}",
                    lines=(
                        f"Created: {created.path}",
                        f"Seeded: {', '.join(created.seeded)}",
                        "Next: run /project-dossier in the new project folder.",
                    ),
                )

            self._start_operation("Creating project", root, create)

        self.push_screen(NewProjectModal(), done)

    def action_add_section(self) -> None:
        if self._busy or not self._inventory_fresh:
            return
        selected = self._selected_project()
        if selected is None or self._inventory is None:
            return
        project_path, name = selected
        drive_map = self._inventory.map
        self._busy = True
        self._work_kind = "prepare"
        self._set_operation(f"Checking available folders for {name}...")
        self.refresh_bindings()
        self._prepare_add_worker(project_path, name, drive_map)

    @work(thread=True, exclusive=True, group="prepare", exit_on_error=False)
    def _prepare_add_worker(self, project_path: Path, name: str, drive_map: DriveMap) -> None:
        try:
            options: list[str] = []
            for section in drive_map.sections:
                if not (project_path / section.id).is_dir():
                    options.append(section.id)
                for child in section.children:
                    if not (project_path / section.id / child).is_dir():
                        options.append(f"{section.id}/{child}")
        except Exception as error:
            self.call_from_thread(self._preparation_failed, "check available folders", error)
            return
        self.call_from_thread(self._show_add_plan, project_path, name, drive_map, options)

    def _show_add_plan(
        self,
        project_path: Path,
        name: str,
        drive_map: DriveMap,
        options: list[str],
    ) -> None:
        self._busy = False
        self._work_kind = None
        self.refresh_bindings()
        if not options:
            self._set_operation(f"{name} already has every mapped folder")
            self.notify("Every mapped folder already exists", title=name)
            return

        def done(picked: list[str] | None) -> None:
            if not picked or self._inventory is None:
                return
            root = self._inventory.root

            def create() -> OperationOutcome:
                fresh_inventory = scan_drive(root)
                fresh_map = fresh_inventory.map
                project_exists = any(project.name == name for project in fresh_inventory.projects)
                if not project_exists:
                    return OperationOutcome(
                        title="Add-folders plan changed",
                        summary=f"{name} is no longer available - no folders created",
                        lines=("Return to the project list and refresh the drive.",),
                        severity="warning",
                    )
                valid = {
                    section.id
                    for section in fresh_map.sections
                } | {
                    f"{section.id}/{child}"
                    for section in fresh_map.sections
                    for child in section.children
                }
                changed = fresh_map != drive_map or any(
                    item not in valid or (project_path / item).is_dir() for item in picked
                )
                if changed:
                    return OperationOutcome(
                        title="Add-folders plan changed",
                        summary=f"{name} changed since preview - no folders created",
                        lines=(
                            "The drive map or project folders changed while the preview was open.",
                            "Run Add folders again to review the current choices.",
                        ),
                        severity="warning",
                    )
                created = add_sections(root, fresh_map, project_path, picked)
                return OperationOutcome(
                    title="Folders created",
                    summary=f"Created {len(created)} folder(s) in {name}",
                    lines=tuple(f"Created: {item}" for item in created) or ("Nothing changed.",),
                )

            self._start_operation("Creating folders", root, create)

        self.push_screen(AddSectionModal(name, options), done)

    def action_clean(self) -> None:
        if self._busy or not self._inventory_fresh:
            return
        selected = self._selected_project()
        if selected is None or self._inventory is None:
            return
        project_path, name = selected
        drive_map = self._inventory.map
        self._busy = True
        self._work_kind = "prepare"
        self._set_operation(f"Finding removable empty folders in {name}...")
        self.refresh_bindings()
        self._prepare_clean_worker(project_path, name, drive_map)

    @work(thread=True, exclusive=True, group="prepare", exit_on_error=False)
    def _prepare_clean_worker(self, project_path: Path, name: str, drive_map: DriveMap) -> None:
        try:
            empties = find_empty_dirs(project_path, drive_map)
        except Exception as error:
            self.call_from_thread(self._preparation_failed, "inspect empty folders", error)
            return
        self.call_from_thread(self._show_clean_plan, project_path, name, empties)

    def _show_clean_plan(self, project_path: Path, name: str, empties: list[str]) -> None:
        self._busy = False
        self._work_kind = None
        self.refresh_bindings()

        def done(confirmed: bool) -> None:
            if not confirmed or self._inventory is None:
                return
            root = self._inventory.root

            def clean() -> OperationOutcome:
                fresh_inventory = scan_drive(root)
                fresh_empties = find_empty_dirs(project_path, fresh_inventory.map)
                if fresh_inventory.map != drive_map or sorted(fresh_empties) != sorted(empties):
                    return OperationOutcome(
                        title="Clean plan changed",
                        summary=f"{name} changed since preview - nothing removed",
                        lines=(
                            "Empty-folder state changed while the preview was open.",
                            "Run Clean again to review the current plan.",
                        ),
                        severity="warning",
                    )
                removed = remove_empty_dirs(root, project_path, fresh_empties)
                return OperationOutcome(
                    title="Empty folders cleaned",
                    summary=f"Removed {len(removed)} empty folder(s) from {name}",
                    lines=tuple(f"Removed: {item}" for item in removed) or ("Nothing changed.",),
                )

            self._start_operation("Removing empty folders", root, clean)

        self.push_screen(
            ConfirmListModal(
                f"Clean empty folders - {name}",
                [f"Remove {item}" for item in empties],
                f"Remove {len(empties)} empty folder(s)",
            ),
            done,
        )

    def action_conform(self) -> None:
        if self._busy or not self._inventory_fresh:
            return
        selected = self._selected_project()
        row = self._selected_row()
        if selected is None or row is None or self._inventory is None:
            return
        project_path, name = selected
        inventory = self._inventory
        drive_map = inventory.map
        original_project = next(project for project in inventory.projects if project.name == name)
        original_token = _project_token(original_project)
        plan = build_plan(row.report, drive_map)
        lines = [
            f"{action.kind.title()}: {action.src + ' -> ' if action.src else ''}{action.dst}"
            + (f" ({action.file_count} files)" if action.file_count else "")
            for action in plan.actions
        ]

        def done(confirmed: bool) -> None:
            if not confirmed:
                return
            root = inventory.root

            def conform() -> OperationOutcome:
                fresh_inventory = scan_drive(root)
                fresh_project = next(
                    (project for project in fresh_inventory.projects if project.name == name),
                    None,
                )
                if fresh_project is None:
                    return OperationOutcome(
                        title="Conform plan changed",
                        summary=f"{name} is no longer available - nothing changed",
                        lines=("Return to the project list and refresh the drive.",),
                        severity="warning",
                    )
                fresh_map = fresh_inventory.map
                fresh_plan = build_plan(report_project(fresh_project, fresh_map), fresh_map)
                if (
                    fresh_map != drive_map
                    or fresh_plan.actions != plan.actions
                    or _project_token(fresh_project) != original_token
                ):
                    changed_lines = tuple(
                        f"{action.kind.title()}: "
                        f"{action.src + ' -> ' if action.src else ''}{action.dst}"
                        for action in fresh_plan.actions
                    )
                    return OperationOutcome(
                        title="Conform plan changed",
                        summary=f"{name} changed since preview - nothing moved",
                        lines=changed_lines
                        or ("Project now follows the current drive map.",),
                        severity="warning",
                    )
                result = apply_plan(root, project_path, fresh_map, fresh_plan)
                done_count = sum(1 for action in result.actions if action.status == DONE)
                skipped = sum(1 for action in result.actions if action.status == SKIPPED)
                conflicts = sum(1 for action in result.actions if action.status == CONFLICT)
                detail = []
                for action in result.actions:
                    source = f"{action.src} -> " if action.src else ""
                    note = f" - {action.note}" if action.note else ""
                    detail.append(
                        f"{(action.status or 'planned').upper()}: "
                        f"{action.kind} {source}{action.dst}{note}"
                    )
                severity = "warning" if conflicts or skipped else "information"
                summary = f"Conformed {name}: {done_count} done, {skipped} skipped"
                if conflicts:
                    summary += f", {conflicts} conflict(s) need review"
                return OperationOutcome(
                    title="Conform result",
                    summary=summary,
                    lines=tuple(detail) or ("Project already follows the drive map.",),
                    severity=severity,
                )

            self._start_operation("Applying conform plan", root, conform)

        self.push_screen(
            ConfirmListModal(
                f"Conform plan - {name}",
                lines,
                f"Apply {len(plan.actions)} repair(s)",
            ),
            done,
        )


def run_tui(drive: Path | None = None) -> int:
    AtlasApp(drive).run()
    return 0
