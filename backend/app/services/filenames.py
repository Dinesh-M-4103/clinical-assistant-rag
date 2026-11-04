"""Sanitising user-supplied file names before they are stored or echoed back."""

import re
import unicodedata

_UNSAFE_CHARS = re.compile(r"[^A-Za-z0-9._() -]+")
_MAX_LENGTH = 120
FALLBACK_FILENAME = "report.pdf"


def sanitize_filename(raw: str | None) -> str:
    """Return a short, ASCII, separator-free ``.pdf`` name for display purposes.

    The result is never used to build a filesystem path (files are stored under
    server-generated ids); sanitising keeps logs, headers and the UI safe.
    """
    leaf = (raw or "").replace("\\", "/").rsplit("/", 1)[-1]
    stem = leaf[:-4] if leaf.lower().endswith(".pdf") else leaf
    ascii_stem = unicodedata.normalize("NFKD", stem).encode("ascii", "ignore").decode()
    cleaned = _UNSAFE_CHARS.sub("_", ascii_stem).strip(" ._")
    if not cleaned:
        return FALLBACK_FILENAME
    return f"{cleaned[: _MAX_LENGTH - 4]}.pdf"
