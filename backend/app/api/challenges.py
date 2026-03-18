"""Challenge API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.models.submission import Submission
from app.services.challenge_service import (
    get_calibration_challenges,
    get_challenge,
    get_challenges,
)

router = APIRouter(tags=["challenges"])


def _strip_solution(challenge: dict) -> dict:
    """Return a copy of the challenge dict without reference_solution."""
    return {k: v for k, v in challenge.items() if k != "reference_solution"}


@router.get("/challenges")
def list_challenges(
    difficulty: str | None = Query(None),
    mode: str | None = Query(None),
    domain: str | None = Query(None),
):
    """List all challenges with optional filters."""
    results = get_challenges(difficulty=difficulty, mode=mode, domain=domain)
    return {
        "challenges": [_strip_solution(c) for c in results],
        "total": len(results),
    }


@router.get("/challenges/calibration")
def list_calibration_challenges():
    """Return the 10 calibration challenges in order."""
    results = get_calibration_challenges()
    return {
        "challenges": [_strip_solution(c) for c in results],
        "total": len(results),
    }


@router.get("/challenges/{challenge_id}")
def get_challenge_by_id(challenge_id: str):
    """Get a single challenge by id (excludes reference_solution)."""
    challenge = get_challenge(challenge_id)
    if challenge is None:
        raise HTTPException(status_code=404, detail="Challenge not found")
    return _strip_solution(challenge)


@router.get("/challenges/{challenge_id}/reference-solution")
async def get_reference_solution(
    challenge_id: str,
    session: AsyncSession = Depends(get_session),
):
    """Get the reference solution for a challenge (requires completion)."""
    challenge = get_challenge(challenge_id)
    if challenge is None:
        raise HTTPException(status_code=404, detail="Challenge not found")

    # Check that the user has completed this challenge
    result = await session.execute(
        select(Submission).where(
            Submission.challenge_id == challenge_id,
            Submission.status == "completed",
        )
    )
    if result.scalar_one_or_none() is None:
        raise HTTPException(status_code=403, detail="Complete the challenge first")

    return {
        "challenge_id": challenge_id,
        "reference_solution": challenge.get("reference_solution", ""),
    }
