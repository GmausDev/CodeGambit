from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class ELOHistory(Base):
    __tablename__ = "elo_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    submission_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("submissions.id"), nullable=False
    )
    dimension: Mapped[str] = mapped_column(String(64), nullable=False)
    elo_before: Mapped[int] = mapped_column(Integer, nullable=False)
    elo_after: Mapped[int] = mapped_column(Integer, nullable=False)
    delta: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class SocraticAnswers(Base):
    __tablename__ = "socratic_answers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    submission_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("submissions.id"), nullable=False
    )
    questions: Mapped[list] = mapped_column(JSON, default=list)
    answers: Mapped[list] = mapped_column(JSON, default=list)
    answer_evaluation: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class CollaborativeSteps(Base):
    __tablename__ = "collaborative_steps"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    submission_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("submissions.id"), nullable=False
    )
    step_number: Mapped[int] = mapped_column(Integer, nullable=False)
    step_code: Mapped[str] = mapped_column(Text, nullable=False)
    step_evaluation: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    step_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
