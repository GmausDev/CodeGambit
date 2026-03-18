from datetime import datetime

from sqlalchemy import JSON, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Challenge(Base):
    __tablename__ = "challenges"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    domain: Mapped[str] = mapped_column(String(64), nullable=False)
    difficulty: Mapped[str] = mapped_column(String(32), nullable=False)
    mode: Mapped[str] = mapped_column(String(32), nullable=False)
    category: Mapped[str] = mapped_column(String(64), nullable=False)
    tags: Mapped[list] = mapped_column(JSON, default=list)
    starter_code: Mapped[str | None] = mapped_column(Text, nullable=True)
    rubric: Mapped[dict] = mapped_column(JSON, default=dict)
    constraints: Mapped[dict] = mapped_column(JSON, default=dict)
    expected_concepts: Mapped[list] = mapped_column(JSON, default=list)
    elo_target: Mapped[int] = mapped_column(Integer, default=1200)
    test_cases: Mapped[list] = mapped_column(JSON, default=list)
    reference_solution: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
