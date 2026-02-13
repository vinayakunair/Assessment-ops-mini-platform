from sqlalchemy import String, DateTime, JSON, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
import uuid
from db import Base


class Attempt(Base):
    __tablename__ = "attempts"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    source_event_id: Mapped[str] = mapped_column(String, unique=True, index=True)

    student: Mapped[dict] = mapped_column(JSON, nullable=False)
    test: Mapped[dict] = mapped_column(JSON, nullable=False)
    answers: Mapped[dict] = mapped_column(JSON, nullable=False)
    raw_payload: Mapped[dict] = mapped_column(JSON, nullable=False)

    channel: Mapped[str] = mapped_column(String, nullable=True)
    status: Mapped[str] = mapped_column(String, default="INGESTED", index=True)

    duplicate_of_attempt_id: Mapped[str | None] = mapped_column(
        String, ForeignKey("attempts.id"), nullable=True, index=True
    )

    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

   
    score = relationship("AttemptScore", back_populates="attempt", uselist=False)
    duplicates = relationship("Attempt", remote_side=[id])


class AttemptScore(Base):
    __tablename__ = "attempt_scores"

    attempt_id: Mapped[str] = mapped_column(
        String, ForeignKey("attempts.id"), primary_key=True, index=True
    )

    correct: Mapped[int] = mapped_column(nullable=False)
    wrong: Mapped[int] = mapped_column(nullable=False)
    skipped: Mapped[int] = mapped_column(nullable=False)
    accuracy: Mapped[float] = mapped_column(nullable=False)
    net_correct: Mapped[int] = mapped_column(nullable=False)
    score: Mapped[float] = mapped_column(nullable=False)

    computed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    explanation: Mapped[dict] = mapped_column(JSON, nullable=False)

    attempt = relationship("Attempt", back_populates="score")


class Flag(Base):
    __tablename__ = "flags"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    attempt_id: Mapped[str] = mapped_column(String, ForeignKey("attempts.id"), index=True)
    reason: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    attempt = relationship("Attempt")
