"""The console's layout rules: Regions, Compositions, and where keys go.

Pure. Given a terminal size and what the operator has collapsed, this decides
which Composition is in force and which Regions are drawn; given a Region, it
decides where Tab, Enter and Escape lead. ``app.py`` applies the answer and owns
nothing of the rule.

The sizes are measured, not assumed: ticket 03 read forty PTY resizes off the
agent runtime and found rows abundant and near-constant at 51, columns scarce and
trimodal, and eight of twelve distinct widths too narrow to hold two columns of
content. See ADR 0005.
"""

from __future__ import annotations

from dataclasses import dataclass

# The three Regions, in drill order: outermost first.
PROJECT_LIST = "projects"
TREE = "tree"
COMPANION = "companion"
REGIONS = (PROJECT_LIST, TREE, COMPANION)

# Compositions.
SPLIT = "split"
SINGLE = "single"
REFUSED = "refused"

# Breakpoints. The horizontal 100 is the one already declared in the app's
# HORIZONTAL_BREAKPOINTS and is reused deliberately; the wordmark's own 115 and 82
# are a different measurement of a different thing and stay independent.
SPLIT_COLUMNS = 100
MIN_COLUMNS = 40
MERGE_ROWS = 30
MIN_ROWS = 16

REFUSAL = "Atlas needs at least 40 columns and 16 rows."


@dataclass(frozen=True)
class Layout:
    """What to draw at one terminal size."""

    composition: str
    visible: tuple[str, ...]
    merge_status: bool = False
    refusal: str = ""


def layout_for(width: int, height: int, *, focus: str = PROJECT_LIST,
               collapsed: frozenset[str] | set[str] = frozenset(),
               zoomed: str | None = None) -> Layout:
    """The Composition a terminal of this size earns, and what it shows.

    An explicit collapse outranks the breakpoint default and is honoured until
    the width cannot carry it, at which point Single-Region takes over and the
    collapse is remembered rather than discarded.
    """
    if width < MIN_COLUMNS or height < MIN_ROWS:
        return Layout(composition=REFUSED, visible=(), refusal=REFUSAL)

    merge = height < MERGE_ROWS
    if zoomed is not None:
        return Layout(composition=SINGLE, visible=(zoomed,), merge_status=merge)
    if width < SPLIT_COLUMNS:
        return Layout(composition=SINGLE, visible=(focus,), merge_status=merge)
    shown = tuple(region for region in REGIONS if region not in collapsed)
    return Layout(composition=SPLIT, visible=shown or (focus,), merge_status=merge)


# ----------------------------------------------------------------- navigation
#
# The navigation model is identical in both Compositions, which is why none of
# these take a width. In Split Composition they move focus; in Single-Region they
# move focus and, because only the focused Region is drawn, also change what is
# on screen. No key changes meaning with width.


def next_region(current: str, *,
                collapsed: frozenset[str] | set[str] = frozenset()) -> str:
    """Where Tab goes from ``current``, skipping anything collapsed."""
    available = [region for region in REGIONS if region not in collapsed]
    if current not in available:
        return available[0] if available else current
    return available[(available.index(current) + 1) % len(available)]


def drill(current: str) -> str:
    """Where Enter goes: one Region deeper, stopping at the innermost."""
    index = REGIONS.index(current)
    return REGIONS[min(index + 1, len(REGIONS) - 1)]


def unwind(current: str) -> str | None:
    """Where Escape goes: one Region out, and ``None`` to leave the project."""
    index = REGIONS.index(current)
    return REGIONS[index - 1] if index else None


# ----------------------------------------------------------- Companion Modes

EXPECTATIONS = "expectations"
HEALTH = "health"
DOSSIER = "dossier"
MODES = (EXPECTATIONS, HEALTH, DOSSIER)

# Unmet Expectations is the default because it is the only mode that has to be
# readable at the same time as the tree - what is filed against what the map
# expects is the comparison the screen exists to make. Project health and the
# dossier are answers to questions the operator asks one at a time, which is what
# makes them modes rather than Regions (ADR 0005).
DEFAULT_MODE = EXPECTATIONS

MODE_LABELS = {
    EXPECTATIONS: "Unmet expectations",
    HEALTH: "Project health",
    DOSSIER: "Dossier",
}


def next_mode(current: str) -> str:
    """Where `d` goes."""
    return MODES[(MODES.index(current) + 1) % len(MODES)]


# ------------------------------------------------------------- the chrome

# What the footer keeps when there is no room for the rest: the keys that move.
# Everything else stays one `?` away, which is why `?` is one of the three.
NAVIGATION_ACTIONS = ("show_help_panel", "next_region", "drill")


def footer_actions(width: int) -> tuple[str, ...] | None:
    """Which bindings the footer may show; ``None`` means all of them.

    Reuses the Split breakpoint rather than introducing a third width constant.
    The cost is real - at 87 columns the action keys drop out of the footer even
    though the terminal is not tiny - and it is the price of not having a third
    set of numbers to keep in agreement.
    """
    return NAVIGATION_ACTIONS if width < SPLIT_COLUMNS else None


def summary_line(region: str, *, drive_summary: str, project: str,
                 companion_mode: str, companion_count: int) -> str:
    """One line answering for whichever Region has focus."""
    if region == COMPANION:
        label = MODE_LABELS.get(companion_mode, companion_mode)
        count = str(companion_count) if companion_count else "none"
        return f"{project} | {label}: {count}"
    if region == TREE:
        return f"{project} | tree"
    return drive_summary
