from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Evaluation(Base):
    __tablename__ = "evaluations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    submission_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("submissions.id"), unique=True, nullable=False
    )
    overall_score: Mapped[int] = mapped_column(Integer, nullable=False)
    architecture_score: Mapped[int] = mapped_column(Integer, nullable=False)
    framework_depth_score: Mapped[int] = mapped_column(Integer, nullable=False)
    complexity_mgmt_score: Mapped[int] = mapped_column(Integer, nullable=False)
    feedback_summary: Mapped[str] = mapped_column(Text, nullable=False)
    strengths: Mapped[list] = mapped_column(JSON, default=list)
    improvements: Mapped[list] = mapped_column(JSON, default=list)
    mode_specific_feedback: Mapped[str | None] = mapped_column(Text, nullable=True)
    raw_ai_response: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    model_used: Mapped[str | None] = mapped_column(String(64), nullable=True)
    tokens_used: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
