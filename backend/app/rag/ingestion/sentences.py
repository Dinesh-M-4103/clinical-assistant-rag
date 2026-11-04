"""Rule-based sentence splitting tuned for clinical prose.

A plain "split on full stop" breaks on ``Dr. Rao``, ``Tab. Metformin`` and
``b.i.d.``; this splitter only breaks where a real sentence start follows.
"""

import re

_BOUNDARY = re.compile(r"(?<=[.!?])\s+(?=[\"'(\[]?[A-Z0-9])")
_ABBREVIATIONS = frozenset(
    {
        "dr", "mr", "mrs", "ms", "prof", "vs", "etc", "approx", "no", "fig", "st", "sr", "jr",
        "dept", "ref", "vol", "cf", "inj", "tab", "cap", "syp", "oint", "sig", "pt", "hosp",
    }
)  # fmt: skip
_DOTTED_ABBREVIATION = re.compile(r"^(?:[a-z]\.)+[a-z]?$", re.IGNORECASE)


def split_sentences(text: str) -> list[str]:
    """Split one paragraph into sentences, keeping abbreviations intact."""
    sentences: list[str] = []
    start = 0
    for match in _BOUNDARY.finditer(text):
        if _ends_with_abbreviation(text[start : match.start()]):
            continue
        sentences.append(text[start : match.start()].strip())
        start = match.end()
    sentences.append(text[start:].strip())
    return [sentence for sentence in sentences if sentence]


def _ends_with_abbreviation(fragment: str) -> bool:
    words = fragment.split()
    last_word = words[-1] if words else ""
    bare = last_word.rstrip(".").lower()
    if len(bare) == 1 and bare.isalpha():
        return True
    return bare in _ABBREVIATIONS or bool(_DOTTED_ABBREVIATION.match(last_word))
