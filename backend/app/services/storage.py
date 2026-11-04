"""On-disk storage of uploaded PDFs: ``<root>/<uhid>/<report_id>.pdf``."""

import re
import shutil
from pathlib import Path
from typing import BinaryIO

from app.core.errors import FileTooLargeError, UnsupportedMediaTypeError
from app.domain import UHID_PATTERN

PDF_MAGIC = b"%PDF-"
_BYTES_PER_MB = 1024 * 1024
_COPY_CHUNK_BYTES = _BYTES_PER_MB
_UHID = re.compile(UHID_PATTERN)
_REPORT_ID = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")


class ReportFileStore:
    """The only code that touches report files.

    Paths are assembled solely from a validated UHID and a server-generated
    UUID, so no client-controlled string can address another location.
    """

    def __init__(self, root: Path, max_upload_mb: int) -> None:
        self._root = root
        self._max_upload_mb = max_upload_mb

    def path_for(self, uhid: str, report_id: str) -> Path:
        if not _UHID.fullmatch(uhid) or not _REPORT_ID.fullmatch(report_id):
            raise ValueError("Refusing to build a storage path from unvalidated identifiers")
        return self._root / uhid / f"{report_id}.pdf"

    def save(self, stream: BinaryIO, uhid: str, report_id: str) -> int:
        """Stream a validated PDF to disk and return its size in bytes.

        The size cap is enforced while copying (never by trusting headers) and
        the file only appears under its final name once fully written.
        """
        head = stream.read(len(PDF_MAGIC))
        if head != PDF_MAGIC:
            raise UnsupportedMediaTypeError("The uploaded file is not a PDF.")

        destination = self.path_for(uhid, report_id)
        destination.parent.mkdir(parents=True, exist_ok=True)
        partial = destination.with_suffix(".part")
        size = len(head)
        try:
            with partial.open("wb") as out:
                out.write(head)
                while chunk := stream.read(_COPY_CHUNK_BYTES):
                    size += len(chunk)
                    if size > self._max_upload_mb * _BYTES_PER_MB:
                        raise FileTooLargeError(self._max_upload_mb)
                    out.write(chunk)
            partial.replace(destination)
        except BaseException:
            partial.unlink(missing_ok=True)
            raise
        return size

    def delete(self, uhid: str, report_id: str) -> None:
        self.path_for(uhid, report_id).unlink(missing_ok=True)

    def delete_patient(self, uhid: str) -> None:
        if not _UHID.fullmatch(uhid):
            raise ValueError("Refusing to delete a directory for an invalid UHID")
        shutil.rmtree(self._root / uhid, ignore_errors=True)
