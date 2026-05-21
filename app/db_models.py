"""SQLAlchemy 2.x ORM models — one class per DB table.

Keep this file free of Pydantic imports. Pydantic schemas live in app/models.py.

The DB-level updated_at triggers from migrations/001_initial_schema.up.sql are
NOT used. Instead, updated_at is maintained by the ORM via column `onupdate`,
which is the SQLAlchemy equivalent of GORM's BeforeUpdate hook.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def _now() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class TimestampMixin:
    """Adds created_at / updated_at / deleted_at to every table.

    updated_at is set automatically by the ORM on every flush that modifies the
    row — no DB trigger required.
    """

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=_now,
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=_now,
        onupdate=_now,
        nullable=False,
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )


class SampleType(TimestampMixin, Base):
    __tablename__ = "sample_types"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    templates: Mapped[list["ExperimentTemplate"]] = relationship(
        back_populates="sample_type"
    )


class ExperimentTemplate(TimestampMixin, Base):
    __tablename__ = "experiment_templates"
    __table_args__ = (UniqueConstraint("sample_type_id", "name"),)

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    sample_type_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("sample_types.id", ondelete="RESTRICT"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    template: Mapped[dict] = mapped_column(JSONB, nullable=False)

    sample_type: Mapped["SampleType"] = relationship(back_populates="templates")


class Experiment(TimestampMixin, Base):
    """One row per experiment ticket. `id` is supplied by Ticketing Service."""

    __tablename__ = "experiments"

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    state: Mapped[dict] = mapped_column(JSONB, nullable=False)
