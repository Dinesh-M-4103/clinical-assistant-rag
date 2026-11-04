"""Version 1 of the HTTP API, mounted under ``/api/v1``."""

from fastapi import APIRouter

from app.api.v1 import chat, health, patients, reports

router = APIRouter(prefix="/api/v1")
router.include_router(health.router)
router.include_router(patients.router)
router.include_router(reports.router)
router.include_router(chat.router)
