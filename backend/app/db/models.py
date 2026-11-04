"""ORM models for patients and their uploaded reports."""

from datetime import datetime

from sqlalchemy import ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, UTCDateTime, utc_now


class Patient(Base):
    __tablename__ = "patients"

    uhid: Mapped[str] = mapped_column(String(32), primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    age: Mapped[int] = mapped_column(Integer)
    gender: Mapped[str] = mapped_column(String(16))
    summary: Mapped[str | None] = mapped_column(Text, default=None)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utc_now)

    # passive_deletes lets the database's ON DELETE CASCADE do the row removal.
    reports: Mapped[list["Report"]] = relationship(
        back_populates="patient", cascade="all, delete-orphan", passive_deletes=True
    )

    @property
    def report_count(self) -> int:
        return len(self.reports)


class Report(Base):
    __tablename__ = "reports"
    __table_args__ = (Index("ix_reports_uhid_uploaded_at", "uhid", "uploaded_at"),)

    report_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    uhid: Mapped[str] = mapped_column(ForeignKey("patients.uhid", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(200))
    category: Mapped[str] = mapped_column(String(32))
    notes: Mapped[str | None] = mapped_column(Text, default=None)
    original_filename: Mapped[str] = mapped_column(String(255))
    page_count: Mapped[int] = mapped_column(Integer)
    chunk_count: Mapped[int] = mapped_column(Integer)
    size_bytes: Mapped[int] = mapped_column(Integer)
    uploaded_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utc_now)

    patient: Mapped[Patient] = relationship(back_populates="reports")
