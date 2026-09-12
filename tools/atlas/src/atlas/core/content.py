"""What is inside a file, for the File Rules that ask (ADR 0009).

Everything else Atlas knows comes from a directory listing. This module is the
one place that opens a file and reads it, so its costs are stated here once:

- **Reading a file on the Drive mount downloads it.** A placeholder hydrates on
  open. Callers only reach this after a file's name has already qualified, and a
  PDF over ``PDF_READ_LIMIT`` is never opened at all.
- **A file Atlas cannot read never matches.** Malformed, truncated, locked with
  a password, or simply not a PDF: all return None, and a rule that cannot be
  evaluated does not move anything. Uncertainty is never a reason to file
  something. A set that is only *permission*-locked - opens without a password,
  refuses editing, the usual state of an issued drawing set - is read normally.
- **Nothing reaches the terminal.** pypdf reports damaged files through the
  ``logging`` module, which with no handler configured prints to stderr - under
  the console, on top of the screen. Its logger is silenced here, on import.

Reads are cached by path, size and modification time, because the Guard
re-derives the report before every write and a drawing set should be downloaded
once, not once per confirmation.
"""

from __future__ import annotations

import logging
import os
import re
import warnings
from functools import lru_cache
from pathlib import Path

from pypdf import PdfReader

from .scan import long_path

# Past this, a PDF is not opened. Big enough for a typical permit set's first
# page to be reachable, small enough that a 900 MB scan of the as-builts is never
# pulled down to answer a filing question. A module constant, not a map key: it
# is a cost limit, not folder structure, and the map is only the latter.
PDF_READ_LIMIT = 64 * 1024 * 1024

# The PDF header may sit anywhere in the first 1024 bytes (ISO 32000-1, 7.5.2).
_HEADER_WINDOW = 1024
_WHITESPACE = re.compile(r"\s+")

_pypdf_log = logging.getLogger("pypdf")
_pypdf_log.addHandler(logging.NullHandler())
_pypdf_log.propagate = False
warnings.filterwarnings("ignore", module=r"pypdf(\..*)?$")


def normalise(text: str) -> str:
    """Casefolded, with every run of whitespace collapsed to one space.

    Applied to both sides of a comparison: extracted title-block text arrives
    with whatever spacing the layout left, and a rule author types a phrase.
    """
    return _WHITESPACE.sub(" ", text.casefold()).strip()


def pdf_text(path: Path) -> str | None:
    """The document title, subject and keywords, then the first page's text.

    Normalised. None when the file is too large, is not a PDF, or cannot be
    read for any reason at all.
    """
    raw = long_path(path)
    try:
        stat = os.stat(raw)
    except OSError:
        return None
    if stat.st_size > PDF_READ_LIMIT:
        return None
    return _pdf_text(raw, stat.st_size, stat.st_mtime_ns)


def clear_cache() -> None:
    _pdf_text.cache_clear()


@lru_cache(maxsize=256)
def _pdf_text(raw: str, size: int, mtime_ns: int) -> str | None:
    # size and mtime_ns are the cache key, not inputs: a changed file is a new key.
    try:
        with open(raw, "rb") as handle:
            if b"%PDF-" not in handle.read(_HEADER_WINDOW):
                return None
            handle.seek(0)
            reader = PdfReader(handle)
            # An empty password opens a permission-only lock and nothing else.
            if reader.is_encrypted and not reader.decrypt(""):
                return None
            parts: list[str] = []
            info = reader.metadata
            if info is not None:
                parts.extend(str(v) for v in (info.title, info.subject, info.get("/Keywords")) if v)
            if len(reader.pages):
                parts.append(reader.pages[0].extract_text() or "")
    except Exception:  # noqa: BLE001 - a damaged PDF can raise almost anything
        return None
    return normalise(" ".join(parts))
