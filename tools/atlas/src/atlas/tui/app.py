"""Atlas TUI - P1 home screen: drive picker + project table with status badges.

A thin view over core.doctor; every number shown here is available identically
from `atlas doctor --json`.
"""

from __future__ import annotations

from pathlib import Path

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.widgets import DataTable, Footer, Header, ListItem, ListView, Static

from ..core.doctor import DriveReport, report_drive
from ..core.scan import discover_drives, scan_drive

BADGES = {"conform": "OK", "drift": "DRIFT", "unfiled": "?", "stub": "STUB"}


class AtlasApp(App):
    TITLE = "Atlas"
    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("r", "refresh", "Refresh"),
        Binding("escape", "back", "Drives"),
    ]
    CSS = """
    #drives { padding: 1 2; }
    DataTable { height: 1fr; }
    #status { dock: bottom; padding: 0 2; color: $text-muted; }
    """

    def __init__(self, drive: Path | None = None) -> None:
        super().__init__()
        self._initial_drive = drive
        self._drives: list[Path] = []
        self._current: Path | None = None

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

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        index = self.query_one("#drives", ListView).index
        if index is not None and 0 <= index < len(self._drives):
            self._open_drive(self._drives[index])

    def _open_drive(self, root: Path) -> None:
        self._current = root
        report = report_drive(scan_drive(root))
        self._fill(report)

    def _fill(self, report: DriveReport) -> None:
        self.query_one("#drives", ListView).display = False
        table = self.query_one("#projects", DataTable)
        table.display = True
        table.clear()
        for p in report.projects:
            table.add_row(
                BADGES.get(p.status, p.status),
                p.name,
                str(p.sections_present),
                "missing " + str(len(p.missing_control_plane)) if p.missing_control_plane else "ok",
                str(len(p.drift) or ""),
                str(len(p.relocations) or ""),
                str(len(p.sweeps) or ""),
                str(len(p.unfiled) or ""),
            )
        counts = report.summary()
        self.sub_title = f"{report.drive} - map v{report.map_version}"
        self.query_one("#status", Static).update(
            f"{counts['conform']} conform / {counts['drift']} drift / "
            f"{counts['unfiled']} unfiled / {counts['stub']} stub - read-only (P1)"
        )
        table.focus()

    def action_refresh(self) -> None:
        if self._current:
            self._open_drive(self._current)
        else:
            self._show_drives()

    def action_back(self) -> None:
        self._show_drives()


def run_tui(drive: Path | None = None) -> int:
    AtlasApp(drive).run()
    return 0
