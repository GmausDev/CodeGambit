"""Challenge API endpoints."""

from fastapi import APIRouter, HTTPException, Query

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
def get_reference_solution(challenge_id: str):
    """Get the reference solution for a challenge."""
    challenge = get_challenge(challenge_id)
    if challenge is None:
        raise HTTPException(status_code=404, detail="Challenge not found")
    return {
        "challenge_id": challenge_id,
        "reference_solution": challenge.get("reference_solution", ""),
    }
