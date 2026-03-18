from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class UserProfile(Base):
    __tablename__ = "user_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)
    display_name: Mapped[str] = mapped_column(String(128), default="Developer")
    elo_overall: Mapped[int] = mapped_column(Integer, default=1200)
    elo_architecture: Mapped[int] = mapped_column(Integer, default=1200)
    elo_framework_depth: Mapped[int] = mapped_column(Integer, default=1200)
    elo_complexity_mgmt: Mapped[int] = mapped_column(Integer, default=1200)
    total_submissions: Mapped[int] = mapped_column(Integer, default=0)
    challenges_completed: Mapped[int] = mapped_column(Integer, default=0)
    calibration_complete: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
