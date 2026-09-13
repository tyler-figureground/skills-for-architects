"""The version Atlas reports is the version it was built as."""

from __future__ import annotations

import tomllib
from pathlib import Path

from atlas import __version__
from atlas.cli import main


def test_reported_version_matches_pyproject():
    pyproject = Path(__file__).resolve().parents[1] / "pyproject.toml"
    declared = tomllib.loads(pyproject.read_text(encoding="utf-8"))["project"]["version"]
    assert __version__ == declared


def test_cli_prints_it(capsys):
    try:
        main(["--version"])
    except SystemExit:
        pass
    assert capsys.readouterr().out.strip() == f"atlas {__version__}"
