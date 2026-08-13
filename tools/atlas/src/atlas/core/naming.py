"""Project naming - parity with New-Project.ps1's Clean-NamePart and folder format."""

from __future__ import annotations

import re
from datetime import date

ILLEGAL = re.compile(r'[\\/:*?"<>|]')  # illegal Windows folder chars -> space
WHITESPACE = re.compile(r"\s+")


def clean_name_part(s: str | None) -> str:
    if not s:
        return ""
    s = ILLEGAL.sub(" ", s.strip())
    s = WHITESPACE.sub(" ", s)
    return s.strip().rstrip(".")


def build_folder_name(created: date, name: str, desc: str = "") -> str:
    """YYMMDD_<Name> or YYMMDD_<Name>-<Descriptor>; parts pre-cleaned."""
    stamp = created.strftime("%y%m%d")
    return f"{stamp}_{name}-{desc}" if desc else f"{stamp}_{name}"
