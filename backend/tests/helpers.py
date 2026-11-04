"""Small builders shared by the API and service tests."""

import json
from io import BytesIO
from typing import Any

import httpx2
from fastapi.testclient import TestClient
from reportlab.pdfgen import canvas

UHID = "MG25001"
ALLOWED_ORIGIN = "http://localhost:5173"


def make_pdf(text: str = "HbA1c 7.8 %") -> bytes:
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer)
    pdf.drawString(72, 720, text)
    pdf.save()
    return buffer.getvalue()


def upload_pdf(
    client: TestClient,
    uhid: str = UHID,
    *,
    content: bytes | None = None,
    filename: str = "cbc.pdf",
    name: str = "CBC Report",
    category: str = "lab",
    notes: str | None = None,
) -> httpx2.Response:
    form = {"name": name, "category": category}
    if notes is not None:
        form["notes"] = notes
    files = {"file": (filename, make_pdf() if content is None else content, "application/pdf")}
    return client.post(f"/api/v1/patients/{uhid}/reports", data=form, files=files)


def parse_sse(body: str) -> list[tuple[str, Any]]:
    """Decode an SSE body into ``(event name, JSON payload)`` pairs, skipping comments."""
    events: list[tuple[str, Any]] = []
    for block in body.replace("\r\n", "\n").strip().split("\n\n"):
        fields = dict(line.split(": ", 1) for line in block.split("\n") if not line.startswith(":"))
        if fields:
            events.append((fields["event"], json.loads(fields["data"])))
    return events
