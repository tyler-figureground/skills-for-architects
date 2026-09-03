"""Enumeration must distinguish "empty" from "could not read".

Atlas's product is what is filed and what is missing, so a folder it failed to
open must never render as a folder with nothing in it. These tests pin the
distinction, and pin the long-path case that produced it on the live studio
drive: two directories over MAX_PATH that their own parents list happily.
"""

from __future__ import annotations

import os
import sys

import pytest

from atlas.core.doctor import report_project
from atlas.core.mapfile import find_map, load_map
from atlas.core.ops import new_project
from atlas.core.scan import (
    READ,
    UNREADABLE,
    Listing,
    list_entries,
    long_path,
    scan_drive,
)

from conftest import make_intake

WINDOWS = sys.platform == "win32"


# ------------------------------------------------------------------ listing


def test_reads_a_directory(tmp_path):
    (tmp_path / "a").mkdir()
    (tmp_path / "b.txt").write_text("x", encoding="utf-8")

    listing = list_entries(tmp_path)

    assert listing.state == READ
    assert listing.readable
    assert listing.error is None
    assert {(e.name, e.is_dir) for e in listing} == {("a", True), ("b.txt", False)}
    assert len(listing) == 2


def test_empty_directory_is_read_not_unreadable(tmp_path):
    (tmp_path / "hollow").mkdir()

    listing = list_entries(tmp_path / "hollow")

    assert listing.state == READ
    assert listing.readable
    assert len(listing) == 0


def test_missing_directory_is_unreadable(tmp_path):
    listing = list_entries(tmp_path / "nope")

    assert listing.state == UNREADABLE
    assert not listing.readable
    assert listing.error
    assert len(listing) == 0


def test_empty_and_unreadable_are_distinguishable(tmp_path):
    """The whole point. Both yield zero entries; only one is trustworthy."""
    (tmp_path / "hollow").mkdir()

    empty = list_entries(tmp_path / "hollow")
    broken = list_entries(tmp_path / "gone")

    assert len(empty) == len(broken) == 0
    assert empty.readable and not broken.readable
    assert empty != broken


def test_listing_iterates_like_the_tuple_it_replaced(tmp_path):
    (tmp_path / "one").mkdir()
    listing = list_entries(tmp_path)

    assert [e.name for e in listing] == ["one"]
    assert {e.name for e in listing} == {"one"}
    assert sum(1 for e in listing if e.is_dir) == 1


def test_unreadable_listing_is_not_falsy_just_because_it_is_empty():
    """`if listing:` must not silently mean `if listing.entries:`."""
    broken = Listing(state=UNREADABLE, error="boom")
    assert bool(broken) is True
    assert not broken.readable


# ---------------------------------------------------------------- long path


def test_long_path_prefixes_only_when_needed(tmp_path):
    short = tmp_path / "short"
    assert long_path(short) == os.fspath(short)


@pytest.mark.skipif(not WINDOWS, reason="MAX_PATH is a Windows limit")
def test_reads_a_directory_past_max_path(tmp_path):
    """Reproduces the live studio-drive failure: 273 chars, parent lists it fine."""
    deep = tmp_path
    while len(os.fspath(deep)) < 300:
        deep = deep / "260104_A-Frame Cabin - Tahoe -Prototype"
    os.makedirs(long_path(deep), exist_ok=True)
    with open(long_path(deep / "sheet.txt"), "w", encoding="utf-8") as fh:
        fh.write("content")

    assert len(os.fspath(deep)) > 260

    listing = list_entries(deep)

    assert listing.readable, f"long path unreadable: {listing.error}"
    assert [e.name for e in listing] == ["sheet.txt"]


# -------------------------------------------------------------------- doctor


def test_scan_records_an_unreadable_project_root(fixture_drive, monkeypatch):
    m = load_map(find_map(fixture_drive))
    new_project(fixture_drive, m, make_intake(fixture_drive, "Alpha"))
    project = next(p for p in fixture_drive.iterdir() if p.name.startswith("2"))

    real = os.scandir

    def deny(path, *a, **kw):
        if os.fspath(path) == os.fspath(project):
            raise PermissionError(13, "denied")
        return real(path, *a, **kw)

    monkeypatch.setattr(os, "scandir", deny)
    inv = scan_drive(fixture_drive)

    entry = next(p for p in inv.projects if p.path == project)
    assert not entry.root_entries.readable


def test_unreadable_project_is_never_reported_conforming(fixture_drive, monkeypatch):
    m = load_map(find_map(fixture_drive))
    new_project(fixture_drive, m, make_intake(fixture_drive, "Alpha"))
    project = next(p for p in fixture_drive.iterdir() if p.name.startswith("2"))

    clean = report_project(next(p for p in scan_drive(fixture_drive).projects
                                if p.path == project), m)
    assert clean.status == "conform"
    assert clean.unreadable == ()

    real = os.scandir

    def deny(path, *a, **kw):
        if os.fspath(path) == os.fspath(project):
            raise PermissionError(13, "denied")
        return real(path, *a, **kw)

    monkeypatch.setattr(os, "scandir", deny)
    broken = report_project(
        next(p for p in scan_drive(fixture_drive).projects if p.path == project), m
    )

    assert broken.unreadable, "the unreadable root must be recorded"
    assert broken.status != "conform"
