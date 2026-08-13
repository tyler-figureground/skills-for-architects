"""Atlas TUI - thin views over core.

Home: drive picker + project table with conformance badges.
Wizards (P2.1): n = new project, a = add section, c = clean empty, f = conform.
Every action here is the same code path as the CLI; the TUI only collects input
and shows plans. Mutations follow the CLI's safety rules because they ARE the
CLI's functions.
"""

from __future__ import annotations

from pathlib import Path

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
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

from ..core.conform import CONFLICT, DONE, Plan, apply_plan, build_plan
from ..core.doctor import DriveReport, report_project
from ..core.mapfile import DriveMap
from ..core.naming import build_folder_name, clean_name_part
from ..core.ops import OpsError, add_sections, find_empty_dirs, new_project, remove_empty_dirs
from ..core.scan import DriveInventory, discover_drives, scan_drive
from datetime import date

BADGES = {"conform": "OK", "drift": "DRIFT", "unfiled": "?", "stub": "STUB"}

MODAL_CSS = """
ModalScreen { align: center middle; }
#dialog {
    width: 72; max-height: 80%; padding: 1 2;
    background: $surface; border: thick $primary;
}
#dialog Input { margin-bottom: 1; }
#dialog SelectionList { max-height: 14; margin-bottom: 1; }
#dialog .actions { height: 3; align-horizontal: right; }
#dialog Button { margin-left: 2; }
#dialog #preview, #dialog #body { color: $text-muted; margin-bottom: 1; }
"""


class NewProjectModal(ModalScreen[tuple[str, str] | None]):
    """Name + descriptor with a live preview of the stamped folder name."""

    def compose(self) -> ComposeResult:
        with Vertical(id="dialog"):
            yield Label("New project")
            yield Input(placeholder="Project name or address", id="name")
            yield Input(placeholder="Descriptor (optional, e.g. ADU, Renovation)", id="desc")
            yield Static("", id="preview")
            with Horizontal(classes="actions"):
                yield Button("Create", variant="primary", id="ok")
                yield Button("Cancel", id="cancel")

    def on_input_changed(self, _: Input.Changed) -> None:
        name = clean_name_part(self.query_one("#name", Input).value)
        desc = clean_name_part(self.query_one("#desc", Input).value)
        preview = build_folder_name(date.today(), name or "<name>", desc)
        self.query_one("#preview", Static).update(f"-> {preview}")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "ok":
            self.dismiss((self.query_one("#name", Input).value,
                          self.query_one("#desc", Input).value))
        else:
            self.dismiss(None)


class AddSectionModal(ModalScreen[list[str] | None]):
    """Multi-select of blessed folders the project does not have yet."""

    def __init__(self, project: str, options: list[str]) -> None:
        super().__init__()
        self._project = project
        self._options = options

    def compose(self) -> ComposeResult:
        with Vertical(id="dialog"):
            yield Label(f"Add folders - {self._project}")
            yield Static("Only map-blessed names are offered; free text does not exist.", id="body")
            yield SelectionList[str](*[(opt, opt) for opt in self._options])
            with Horizontal(classes="actions"):
                yield Button("Create selected", variant="primary", id="ok")
                yield Button("Cancel", id="cancel")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "ok":
            self.dismiss(list(self.query_one(SelectionList).selected))
        else:
            self.dismiss(None)


class ConfirmListModal(ModalScreen[bool]):
    """Generic 'here is the plan - do it?' modal (clean + conform)."""

    def __init__(self, title: str, lines: list[str], ok_label: str) -> None:
        super().__init__()
        self._title = title
        self._lines = lines
        self._ok = ok_label

    def compose(self) -> ComposeResult:
        with Vertical(id="dialog"):
            yield Label(self._title)
            yield Static("\n".join(self._lines) or "(nothing to do)", id="body")
            with Horizontal(classes="actions"):
                if self._lines:
                    yield Button(self._ok, variant="warning", id="ok")
                yield Button("Close", id="cancel")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.dismiss(event.button.id == "ok")


class AtlasApp(App):
    TITLE = "Atlas"
    CSS = MODAL_CSS + """
    #drives { padding: 1 2; }
    DataTable { height: 1fr; }
    #status { dock: bottom; padding: 0 2; color: $text-muted; }
    """
    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("r", "refresh", "Refresh"),
        Binding("n", "new_project", "New"),
        Binding("a", "add_section", "Add"),
        Binding("c", "clean", "Clean"),
        Binding("f", "conform", "Conform"),
        Binding("escape", "back", "Drives"),
    ]

    def __init__(self, drive: Path | None = None) -> None:
        super().__init__()
        self._initial_drive = drive
        self._drives: list[Path] = []
        self._inventory: DriveInventory | None = None
        self._row_names: list[str] = []

    # ------------------------------------------------------------- lifecycle

    def compose(self) -> ComposeResult:
        yield Header()
        yield Vertical(ListView(id="drives"), DataTable(id="projects"), Static(id="status"))
        yield Footer()

    def on_mount(self) -> None:
        table = self.query_one("#projects", DataTable)
        table.add_columns("Status", "Project", "Sections", "Control plane", "Drift", "Reloc", "Sweep", "Unfiled")
        table.cursor_type = "row"
        table.display = False
        if self._initial_drive:
            self._open_drive(self._initial_drive)
        else:
            self._show_drives()

    # ------------------------------------------------------------- drives

    def _show_drives(self) -> None:
        self._drives = discover_drives()
        lv = self.query_one("#drives", ListView)
        lv.clear()
        for d in self._drives:
            lv.append(ListItem(Static(d.name)))
        lv.display = True
        self.query_one("#projects", DataTable).display = False
        self.query_one("#status", Static).update(
            f"{len(self._drives)} mapped drive(s). Enter to open."
            if self._drives else "No mapped drives found. Set ATLAS_MOUNT_ROOT or pass --drive."
        )
        if len(self._drives) == 1:
            self._open_drive(self._drives[0])

    def on_list_view_selected(self, _: ListView.Selected) -> None:
        index = self.query_one("#drives", ListView).index
        if index is not None and 0 <= index < len(self._drives):
            self._open_drive(self._drives[index])

    def _open_drive(self, root: Path) -> None:
        self._inventory = scan_drive(root)
        self._fill()

    # ------------------------------------------------------------- table

    def _fill(self) -> None:
        assert self._inventory is not None
        inv = self._inventory
        report = DriveReport(
            root=inv.root, drive=inv.map.drive, map_version=inv.map.version,
            projects=tuple(report_project(p, inv.map) for p in inv.projects),
        )
        self.query_one("#drives", ListView).display = False
        table = self.query_one("#projects", DataTable)
        table.display = True
        table.clear()
        self._row_names = []
        for p in report.projects:
            self._row_names.append(p.name)
            table.add_row(
                BADGES.get(p.status, p.status), p.name, str(p.sections_present),
                "missing " + str(len(p.missing_control_plane)) if p.missing_control_plane else "ok",
                str(len(p.drift) or ""), str(len(p.relocations) or ""),
                str(len(p.sweeps) or ""), str(len(p.unfiled) or ""),
            )
        counts = report.summary()
        self.sub_title = f"{report.drive} - map v{report.map_version}"
        self.query_one("#status", Static).update(
            f"{counts['conform']} conform / {counts['drift']} drift / "
            f"{counts['unfiled']} unfiled / {counts['stub']} stub"
        )
        table.focus()

    def _selected_project(self) -> tuple[Path, str] | None:
        if self._inventory is None or not self._row_names:
            return None
        row = self.query_one("#projects", DataTable).cursor_row
        if row is None or row >= len(self._row_names):
            return None
        name = self._row_names[row]
        return self._inventory.root / name, name

    def _refresh_after(self, message: str) -> None:
        self.notify(message)
        self.action_refresh()

    # ------------------------------------------------------------- actions

    def action_refresh(self) -> None:
        if self._inventory is not None:
            self._open_drive(self._inventory.root)
        else:
            self._show_drives()

    def action_back(self) -> None:
        self._show_drives()

    def action_new_project(self) -> None:
        if self._inventory is None:
            return

        def done(result: tuple[str, str] | None) -> None:
            if not result:
                return
            inv = self._inventory
            try:
                created = new_project(inv.root, inv.map, result[0], result[1])
            except OpsError as e:
                self.notify(str(e), severity="error")
                return
            self._refresh_after(f"created {created.folder_name}")

        self.push_screen(NewProjectModal(), done)

    def action_add_section(self) -> None:
        selected = self._selected_project()
        if not selected or self._inventory is None:
            return
        project_path, name = selected
        m = self._inventory.map
        options = []
        for section in m.sections:
            if not (project_path / section.id).is_dir():
                options.append(section.id)
            for child in section.children:
                if not (project_path / section.id / child).is_dir():
                    options.append(f"{section.id}/{child}")

        def done(picked: list[str] | None) -> None:
            if not picked:
                return
            try:
                created = add_sections(self._inventory.root, m, project_path, picked)
            except OpsError as e:
                self.notify(str(e), severity="error")
                return
            self._refresh_after(f"created {len(created)} folder(s) in {name}")

        self.push_screen(AddSectionModal(name, options), done)

    def action_clean(self) -> None:
        selected = self._selected_project()
        if not selected or self._inventory is None:
            return
        project_path, name = selected
        m = self._inventory.map
        empties = find_empty_dirs(project_path, m)

        def done(confirmed: bool) -> None:
            if not confirmed:
                return
            removed = remove_empty_dirs(self._inventory.root, project_path, empties)
            self._refresh_after(f"removed {len(removed)} empty folder(s) from {name}")

        self.push_screen(
            ConfirmListModal(f"Clean empty - {name}", [f"remove: {e}" for e in empties],
                             f"Remove {len(empties)}"),
            done,
        )

    def action_conform(self) -> None:
        selected = self._selected_project()
        if not selected or self._inventory is None:
            return
        project_path, name = selected
        inv = self._inventory
        m = inv.map
        proj_inv = next(p for p in inv.projects if p.name == name)
        plan = build_plan(report_project(proj_inv, m), m)
        lines = [
            f"{a.kind:9} {a.src + ' -> ' if a.src else ''}{a.dst}"
            + (f" ({a.file_count} files)" if a.file_count else "")
            for a in plan.actions
        ]

        def done(confirmed: bool) -> None:
            if not confirmed:
                return
            result = apply_plan(inv.root, project_path, m, plan)
            done_n = sum(1 for a in result.actions if a.status == DONE)
            conflicts = sum(1 for a in result.actions if a.status == CONFLICT)
            message = f"conform {name}: {done_n} done"
            if conflicts:
                message += f", {conflicts} conflict(s) left in place"
            self._refresh_after(message)

        self.push_screen(
            ConfirmListModal(f"Conform plan - {name}", lines, f"Apply {len(plan.actions)}"),
            done,
        )


def run_tui(drive: Path | None = None) -> int:
    AtlasApp(drive).run()
    return 0
