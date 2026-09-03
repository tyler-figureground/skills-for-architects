"""The SOLID+VOID ATLAS header.

Geometry is the thing worth testing. A wordmark that renders the wrong number of
rows silently eats a third of a laptop terminal, and a width rule that picks the
wrong composition clips the mark rather than failing loudly. Colour is already
covered by the token tests, so these assert shape, packing and the width rule.
"""

from __future__ import annotations

import pytest
from rich.text import Text

from atlas.tui.wordmark import (
    BAR,
    COMPACT,
    FULL,
    HALF_BLOCK,
    PIXEL_ROWS,
    composition_for,
    mark_width,
    render_mark,
)

FULL_WORD = "SOLID+VOID ATLAS"


# ---------------------------------------------------------------- geometry


def test_full_mark_is_four_rows():
    """Six pixel rows packed two-per-character-row, plus one row of extrusion."""
    lines = render_mark(FULL).plain.rstrip("\n").split("\n")
    assert len(lines) == 4


def test_compact_mark_is_also_four_rows():
    lines = render_mark(COMPACT).plain.rstrip("\n").split("\n")
    assert len(lines) == 4


def test_bar_is_one_row():
    lines = render_mark(BAR).plain.rstrip("\n").split("\n")
    assert len(lines) == 1


def test_half_block_packing_halves_the_pixel_rows():
    assert PIXEL_ROWS == 6
    # 6 pixel rows + 2 of extrusion = 8 pixels = 4 character rows
    assert (PIXEL_ROWS + 2) // 2 == 4


def test_every_cell_is_the_half_block():
    """Foreground paints the top pixel, background the bottom. Any other glyph
    means the packing broke and the mark is only half resolution."""
    body = render_mark(FULL).plain.rstrip("\n").replace("\n", "")
    assert set(body) == {HALF_BLOCK}


def test_rows_are_rectangular():
    for composition in (FULL, COMPACT):
        lines = render_mark(composition).plain.rstrip("\n").split("\n")
        assert len({len(line) for line in lines}) == 1, f"{composition} is ragged"


def test_mark_is_rich_text_not_str():
    """Textual renders str through from_markup; a Text carries the gradient and
    cannot be mangled by a stray bracket."""
    assert isinstance(render_mark(FULL), Text)


# ------------------------------------------------------------------- widths


def test_declared_widths_match_what_is_rendered():
    for composition in (FULL, COMPACT, BAR):
        line = render_mark(composition).plain.rstrip("\n").split("\n")[0]
        assert len(line) == mark_width(composition), f"{composition} width lies"


def test_full_is_wider_than_compact_is_wider_than_bar():
    assert mark_width(FULL) > mark_width(COMPACT) > mark_width(BAR)


def test_compact_fits_a_laptop_terminal():
    """The whole reason the compact composition exists."""
    assert mark_width(COMPACT) <= 96


def test_bar_fits_the_narrowest_terminal_atlas_supports():
    assert mark_width(BAR) <= 80


# --------------------------------------------------------------- width rule


@pytest.mark.parametrize(
    "columns,expected",
    [
        (200, FULL),
        (120, FULL),
        (115, FULL),
        (114, COMPACT),
        (96, COMPACT),
        (82, COMPACT),
        (81, BAR),
        (80, BAR),
        (40, BAR),
        (1, BAR),
    ],
)
def test_composition_for_width(columns, expected):
    assert composition_for(columns) is expected


def test_every_chosen_composition_actually_fits():
    """The rule must never pick a mark wider than the terminal it was given."""
    for columns in range(20, 240):
        chosen = composition_for(columns)
        assert mark_width(chosen) <= columns, (
            f"at {columns} cols the rule picked {chosen} at {mark_width(chosen)} wide"
        )


# -------------------------------------------------------------------- words


def test_the_mark_reads_solid_void_atlas():
    """Regression: an earlier prototype had VOID and ATLAS running together."""
    from atlas.tui.wordmark import COMPOSITIONS

    assert COMPOSITIONS[FULL].word == FULL_WORD
    assert COMPOSITIONS[COMPACT].word == "SOLID+VOID"
    assert COMPOSITIONS[COMPACT].caption == "ATLAS"
    assert "SOLID+VOID ATLAS" in render_mark(BAR).plain


def test_word_space_separates_more_than_a_letter_gap():
    from atlas.tui.wordmark import GAP, GLYPHS

    assert len(GLYPHS[" "][0]) + 2 * GAP > 2 * GAP + 1
