from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.models.elo_history import ELOHistory
from app.models.submission import Submission
from app.models.user import UserProfile
from app.schemas.user import ELOHistoryOut, UserProfileOut
from app.services.calibration import CalibrationService
from app.services.elo import ELOService

router = APIRouter(prefix="/api/user", tags=["user"])

elo_service = ELOService()
calibration_service = CalibrationService()


@router.get("/profile", response_model=UserProfileOut)
async def get_profile(session: AsyncSession = Depends(get_session)):
    """Return the default user profile (id=1)."""
    result = await session.execute(
        select(UserProfile).where(UserProfile.id == 1)
    )
    user = result.scalar_one()
    return user


@router.get("/elo-history", response_model=list[ELOHistoryOut])
async def get_elo_history(
    dimension: str | None = Query(None, description="Filter by ELO dimension"),
    session: AsyncSession = Depends(get_session),
):
    """Return ELO history records, optionally filtered by dimension."""
    records = await elo_service.get_history(session, dimension=dimension)
    return records


@router.post("/calibrate")
async def calibrate(
    calibration_step: int = Query(0, ge=0, description="Current calibration step"),
    session: AsyncSession = Depends(get_session),
):
    """Start or continue calibration. Step 0 starts fresh; other steps continue."""
    if calibration_step == 0:
        result = await calibration_service.start_calibration(session, user_id=1)
    else:
        result = await calibration_service.get_next_challenge(
            session, user_id=1, calibration_step=calibration_step
        )
    await session.commit()
    return result


@router.get("/stats")
async def get_stats(session: AsyncSession = Depends(get_session)):
    """Aggregated user stats: submission count, completion rate, ELO range."""
    user_result = await session.execute(
        select(UserProfile).where(UserProfile.id == 1)
    )
    user = user_result.scalar_one()

    # Count total submissions
    sub_count_result = await session.execute(
        select(func.count(Submission.id))
    )
    total_submissions = sub_count_result.scalar() or 0

    # Count completed submissions (status = 'evaluated')
    completed_result = await session.execute(
        select(func.count(Submission.id)).where(Submission.status == "evaluated")
    )
    completed = completed_result.scalar() or 0

    completion_rate = round(completed / total_submissions, 2) if total_submissions > 0 else 0.0

    elo_values = [
        user.elo_overall,
        user.elo_architecture,
        user.elo_framework_depth,
        user.elo_complexity_mgmt,
    ]

    return {
        "total_submissions": total_submissions,
        "challenges_completed": user.challenges_completed,
        "completion_rate": completion_rate,
        "calibration_complete": user.calibration_complete,
        "elo_average": round(sum(elo_values) / len(elo_values)),
        "elo_min": min(elo_values),
        "elo_max": max(elo_values),
        "elo_breakdown": {
            "overall": user.elo_overall,
            "architecture": user.elo_architecture,
            "framework_depth": user.elo_framework_depth,
            "complexity_mgmt": user.elo_complexity_mgmt,
        },
    }
