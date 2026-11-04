"""Concurrent uploads, driven through the real HTTP stack."""

import threading
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path

from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app
from app.rag.types import IngestResult
from tests.fakes import FakePipeline
from tests.helpers import UHID, upload_pdf


@dataclass
class SlowPipeline(FakePipeline):
    """Counts how many ingestions overlap in time."""

    active: int = 0
    peak: int = 0
    _guard: threading.Lock = field(default_factory=threading.Lock)

    def ingest_pdf(
        self,
        *,
        patient_id: str,
        report_id: str,
        report_name: str,
        category: str,
        pdf_path: Path,
    ) -> IngestResult:
        with self._guard:
            self.active += 1
            self.peak = max(self.peak, self.active)
        time.sleep(0.05)
        try:
            return super().ingest_pdf(
                patient_id=patient_id,
                report_id=report_id,
                report_name=report_name,
                category=category,
                pdf_path=pdf_path,
            )
        finally:
            with self._guard:
                self.active -= 1


def test_uploads_for_one_patient_never_ingest_concurrently(settings: Settings) -> None:
    pipeline = SlowPipeline()
    with TestClient(create_app(settings, lambda _: pipeline)) as client:
        client.post(
            "/api/v1/patients",
            json={"uhid": UHID, "name": "Asha Verma", "age": 54, "gender": "female"},
        )

        with ThreadPoolExecutor(max_workers=4) as pool:
            responses = list(pool.map(lambda _: upload_pdf(client), range(4)))

        assert [r.status_code for r in responses] == [201] * 4
        assert pipeline.peak == 1
        assert client.get(f"/api/v1/patients/{UHID}").json()["report_count"] == 4
