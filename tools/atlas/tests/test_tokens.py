"""The token layer is the single source of truth for how Atlas looks.

Tests assert on structure, coverage and contrast - never on a literal hex. A test
that pins `#E2452A` breaks every time the palette is tuned and proves nothing; a
test that pins "every state a node can be in has a legible colour" survives
retuning and is the thing that actually matters.
"""

from __future__ import annotations

import pytest

from atlas.core.scan import PARTIAL, READ, UNREADABLE
from atlas.tui import tokens
from atlas.tui.tokens import (
    DRIFTED,
    FILING_STATES,
    LOAD_STATES,
    LOOSE,
    MAPPED,
    MISPLACED,
    UNFILED,
    contrast_ratio,
    filing_style,
    load_style,
    stylesheet,
)

PALETTE = tokens.PALETTE


# --------------------------------------------------------------- coverage


def test_every_filing_state_has_a_style():
    for state in FILING_STATES:
        style = filing_style(state)
        assert style.glyph, f"{state} has no glyph"
        assert style.colour.startswith("#"), f"{state} has no colour"
        assert style.label, f"{state} has no human label"


def test_every_load_state_has_a_disclosure_marker():
    for state in LOAD_STATES:
        assert load_style(state).suffix, f"{state} has no marker"


def test_only_a_fully_read_folder_goes_unannotated():
    """Read is the normal case and needs no words. Every other state says why."""
    assert load_style(READ).label == ""
    for state in (tokens.UNREAD, UNREADABLE, PARTIAL):
        assert load_style(state).label, f"{state} must explain itself"


def test_load_states_match_the_core_constants():
    """The token layer must not invent a second vocabulary for Load State."""
    assert set(LOAD_STATES) == {READ, UNREADABLE, PARTIAL, tokens.UNREAD}


def test_unknown_state_raises_rather_than_rendering_blank():
    with pytest.raises(KeyError):
        filing_style("not-a-state")


# ------------------------------------------------------------- the reading


def test_only_mapped_is_solid():
    """Solid versus hatched is what answers 'is anything wrong here'. ADR 0004."""
    assert filing_style(MAPPED).solid
    for state in (DRIFTED, MISPLACED, LOOSE, UNFILED):
        assert not filing_style(state).solid, f"{state} must not read as filed"


def test_atlas_fixable_states_share_one_colour():
    """Colour answers 'can Atlas fix it, or is it mine'."""
    fixable = {filing_style(s).colour for s in (DRIFTED, MISPLACED, LOOSE)}
    assert len(fixable) == 1
    assert filing_style(UNFILED).colour not in fixable
    assert filing_style(MAPPED).colour not in fixable


def test_unreadable_never_reads_as_empty():
    """The bug this whole model exists to prevent."""
    assert load_style(UNREADABLE).label.strip()
    assert load_style(UNREADABLE).label != load_style(READ).label


# ----------------------------------------------------------------- legible


def _text_tokens():
    return {
        "bone": PALETTE.bone,
        "ink": PALETTE.ink,
        "muted": PALETTE.muted,
        **{s: filing_style(s).colour for s in FILING_STATES},
        **{s: PALETTE.status[s] for s in PALETTE.status},
    }


@pytest.mark.parametrize("name", sorted(_text_tokens()))
def test_text_tokens_are_legible_on_the_ground(name):
    ratio = contrast_ratio(_text_tokens()[name], PALETTE.ground)
    assert ratio >= 4.5, f"{name} is {ratio:.2f}:1 against the ground, needs 4.5"


def test_structural_tokens_are_visible_but_recede():
    for name in ("rail", "dim"):
        ratio = contrast_ratio(getattr(PALETTE, name), PALETTE.ground)
        assert ratio >= 1.2, f"{name} is invisible at {ratio:.2f}:1"
        assert ratio < 4.5, f"{name} is structural and should not compete with text"


def test_the_cursor_is_the_brightest_thing_on_screen():
    ground = PALETTE.ground
    cursor = contrast_ratio(PALETTE.bone, ground)
    for name in ("ink", "muted"):
        assert cursor > contrast_ratio(getattr(PALETTE, name), ground)


def test_contrast_ratio_is_symmetric_and_bounded():
    assert contrast_ratio("#FFFFFF", "#000000") == pytest.approx(21.0, abs=0.05)
    assert contrast_ratio("#000000", "#FFFFFF") == pytest.approx(21.0, abs=0.05)
    assert contrast_ratio("#777777", "#777777") == pytest.approx(1.0, abs=0.01)


# --------------------------------------------------------------- stylesheet


def test_stylesheet_is_generated_from_the_palette_not_written_twice():
    css = stylesheet()
    assert PALETTE.ground in css
    assert PALETTE.bone in css
    assert PALETTE.rail in css


def test_stylesheet_has_no_stray_colour_literals():
    """Every colour in the CSS must come from the palette."""
    import re

    known = {v.lower() for v in vars(PALETTE).values() if isinstance(v, str)}
    known |= {c.lower() for c in PALETTE.status.values()}
    known |= {filing_style(s).colour.lower() for s in FILING_STATES}
    known |= {c.lower() for c in PALETTE.ember}
    for found in re.findall(r"#[0-9A-Fa-f]{6}", stylesheet()):
        assert found.lower() in known, f"{found} is not a palette token"


def test_ember_ramp_runs_light_to_dark():
    lums = [tokens.relative_luminance(c) for c in PALETTE.ember]
    assert lums == sorted(lums, reverse=True), "the ramp must descend"
