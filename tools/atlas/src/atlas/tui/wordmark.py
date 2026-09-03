"""The SOLID+VOID ATLAS header.

Half-block packing is what makes the mark affordable. A terminal cell is roughly
twice as tall as it is wide, and U+2580 UPPER HALF BLOCK splits it: the foreground
paints the top half, the background the bottom. Every character row therefore
carries two pixel rows of letterform, so a six-pixel glyph occupies three rows and
the extrusion adds a fourth. Drawn as whole blocks the same mark costs seven rows,
and the gradient gets one band fewer because there are fewer rows to sample.

Three compositions, chosen by terminal width. The mark greets you at full size
where there is room, sets ATLAS beside it as caption where there is not, and
collapses to a single knocked-out bar on a laptop.
"""

from __future__ import annotations

from dataclasses import dataclass

from rich.text import Text

from . import tokens

HALF_BLOCK = "▀"

# Glyphs are six pixel rows tall and five columns wide. Only the characters the
# mark needs; a wider set earns its place when a second drive name does.
PIXEL_ROWS = 6
GAP = 2

GLYPHS: dict[str, list[str]] = {
    "S": ["#####", "#    ", "#####", "    #", "    #", "#####"],
    "O": ["#####", "#   #", "#   #", "#   #", "#   #", "#####"],
    "L": ["#    ", "#    ", "#    ", "#    ", "#    ", "#####"],
    "I": ["#####", "  #  ", "  #  ", "  #  ", "  #  ", "#####"],
    "D": ["#### ", "#   #", "#   #", "#   #", "#   #", "#### "],
    "V": ["#   #", "#   #", "#   #", "#   #", " # # ", "  #  "],
    "A": ["#####", "#   #", "#   #", "#####", "#   #", "#   #"],
    "T": ["#####", "  #  ", "  #  ", "  #  ", "  #  ", "  #  "],
    # The plus is the cut, and it is drawn heavy on purpose.
    "+": ["     ", "  #  ", "#####", "#####", "  #  ", "     "],
    # Four columns, and it still takes the gaps either side, so VOID and ATLAS
    # separate by eight columns and never read as one word.
    " ": ["    ", "    ", "    ", "    ", "    ", "    "],
}

FULL = "full"
COMPACT = "compact"
BAR = "bar"

# Extrusion depth in pixel rows. Two pixels is one character row of shadow.
_DEPTH = 2

# The console pads two columns each side; the width rule has to respect that or
# the mark renders flush against the terminal edge.
MARGIN = 4

_BAR_TEXT = "  SOLID+VOID ATLAS  "


@dataclass(frozen=True)
class Composition:
    word: str
    caption: str | None = None


COMPOSITIONS: dict[str, Composition] = {
    FULL: Composition("SOLID+VOID ATLAS"),
    COMPACT: Composition("SOLID+VOID", caption="ATLAS"),
    BAR: Composition(_BAR_TEXT),
}


def _stamp(word: str) -> list[list[bool]]:
    grid: list[list[bool]] = [[] for _ in range(PIXEL_ROWS)]
    for index, char in enumerate(word):
        glyph = GLYPHS[char]
        for row in range(PIXEL_ROWS):
            grid[row].extend(cell == "#" for cell in glyph[row])
        if index < len(word) - 1:
            for row in range(PIXEL_ROWS):
                grid[row].extend([False] * GAP)
    return grid


def _ramp(position: float) -> str:
    stops = tokens.PALETTE.ember
    position = max(0.0, min(1.0, position))
    span = 1.0 / (len(stops) - 1)
    index = min(int(position / span), len(stops) - 2)
    local = (position - index * span) / span
    a = tokens.PALETTE.ember[index].lstrip("#")
    b = tokens.PALETTE.ember[index + 1].lstrip("#")
    channels = (
        round(int(a[i : i + 2], 16) + (int(b[i : i + 2], 16) - int(a[i : i + 2], 16)) * local)
        for i in (0, 2, 4)
    )
    return "#%02X%02X%02X" % tuple(channels)


def _shade(depth: int) -> str:
    """Extrusion tone. The layer nearest the face catches a little more light."""
    base = tokens.PALETTE.ground.lstrip("#")
    toward = tokens.PALETTE.ember[4].lstrip("#")
    weight = 0.20 + 0.25 * (_DEPTH - depth) / max(_DEPTH, 1)
    channels = (
        round(int(base[i : i + 2], 16)
              + (int(toward[i : i + 2], 16) - int(base[i : i + 2], 16)) * weight)
        for i in (0, 2, 4)
    )
    return "#%02X%02X%02X" % tuple(channels)


def mark_width(composition: str = FULL) -> int:
    """Width in character columns, without rendering."""
    spec = COMPOSITIONS[composition]
    if composition == BAR:
        return len(spec.word)
    width = len(_stamp(spec.word)[0]) + _DEPTH
    if spec.caption:
        width += 3 + len(spec.caption)
    return width


def composition_for(columns: int, margin: int = MARGIN) -> str:
    """Widest composition that fits, never one that would clip.

    ``margin`` is the console's own horizontal padding. A mark sitting flush
    against both edges of the terminal reads as broken rather than as full-bleed,
    so the thresholds are the mark's width plus that padding: 115 and 82 columns
    for marks that are 111 and 78 wide.
    """
    for candidate in (FULL, COMPACT):
        if columns >= mark_width(candidate) + margin:
            return candidate
    return BAR


def render_mark(composition: str = FULL) -> Text:
    """The mark as Rich Text.

    Never a str: Textual runs ``Text.from_markup`` on strings, and a mark built
    from a hundred colour spans has no business going through a markup parser.
    """
    spec = COMPOSITIONS[composition]
    if composition == BAR:
        out = Text()
        out.append(spec.word, style=f"bold {tokens.PALETTE.ground} on {tokens.PALETTE.ember[2]}")
        return out

    mask = _stamp(spec.word)
    width = len(mask[0])
    rows = PIXEL_ROWS + _DEPTH
    cols = width + _DEPTH
    pixels: list[list[str | None]] = [[None] * cols for _ in range(rows)]

    for depth in range(_DEPTH, 0, -1):
        tone = _shade(depth)
        for row in range(PIXEL_ROWS):
            for col in range(width):
                if mask[row][col]:
                    pixels[row + depth][col + depth] = tone

    for row in range(PIXEL_ROWS):
        colour = _ramp(row / (PIXEL_ROWS - 1))
        for col in range(width):
            if mask[row][col]:
                pixels[row][col] = colour

    if rows % 2:
        pixels.append([None] * cols)

    ground = tokens.PALETTE.ground
    caption_row = 1  # optical centre of a four-row mark
    out = Text()
    for pair in range(len(pixels) // 2):
        top, bottom = pixels[pair * 2], pixels[pair * 2 + 1]
        for col in range(cols):
            out.append(
                HALF_BLOCK,
                style=f"{top[col] or ground} on {bottom[col] or ground}",
            )
        if spec.caption and pair == caption_row:
            out.append("   " + spec.caption, style=f"bold {tokens.PALETTE.ember[1]}")
        elif spec.caption:
            # keep the block rectangular so callers can measure any row
            out.append(" " * (3 + len(spec.caption)))
        out.append("\n")
    return out
