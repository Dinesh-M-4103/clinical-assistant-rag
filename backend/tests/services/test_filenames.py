import pytest

from app.services.filenames import FALLBACK_FILENAME, sanitize_filename


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("cbc.pdf", "cbc.pdf"),
        ("CBC Report (final).PDF", "CBC Report (final).pdf"),
        ("lab results", "lab results.pdf"),
        ("C:\\Users\\me\\scan.pdf", "scan.pdf"),
        ("../../etc/passwd", "passwd.pdf"),
        ("nul\x00byte.pdf", "nul_byte.pdf"),
        ("rapport médical.pdf", "rapport medical.pdf"),
        ("a<b>:c|d.pdf", "a_b_c_d.pdf"),
    ],
)
def test_sanitize_filename(raw: str, expected: str) -> None:
    assert sanitize_filename(raw) == expected


@pytest.mark.parametrize("raw", [None, "", "   ", "...", ".pdf", "日本語.pdf", "/"])
def test_unusable_names_fall_back(raw: str | None) -> None:
    assert sanitize_filename(raw) == FALLBACK_FILENAME


def test_long_names_are_truncated_but_keep_the_extension() -> None:
    result = sanitize_filename("a" * 500 + ".pdf")

    assert len(result) == 120
    assert result.endswith(".pdf")
