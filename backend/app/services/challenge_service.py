"""Business logic for challenge queries and recommendations."""

from typing import Any

from app.services.challenge_loader import get_all_challenges, get_challenge_by_id


def get_challenges(
    difficulty: str | None = None,
    mode: str | None = None,
    domain: str | None = None,
) -> list[dict[str, Any]]:
    """Return all challenges, optionally filtered by difficulty, mode, and domain."""
    challenges = list(get_all_challenges().values())

    if difficulty:
        challenges = [c for c in challenges if c.get("difficulty") == difficulty]
    if mode:
        challenges = [c for c in challenges if c.get("mode") == mode]
    if domain:
        challenges = [c for c in challenges if c.get("domain") == domain]

    return challenges


def get_challenge(challenge_id: str) -> dict[str, Any] | None:
    """Return a single challenge by id."""
    return get_challenge_by_id(challenge_id)


def get_recommendations(
    user_elo: int,
    completed_ids: list[str],
) -> list[dict[str, Any]]:
    """Return challenges within the user's ELO band, excluding completed ones.

    ELO band: [user_elo - 200, user_elo + 200].
    Results are sorted by proximity to user_elo (closest first).
    """
    elo_min = user_elo - 200
    elo_max = user_elo + 200
    completed_set = set(completed_ids)

    candidates = []
    for c in get_all_challenges().values():
        if c["id"] in completed_set:
            continue
        elo_target = c.get("elo_band", c.get("elo_target", 1200))
        if elo_min <= elo_target <= elo_max:
            candidates.append(c)

    # Sort by distance from user_elo (closest first)
    candidates.sort(key=lambda c: abs(c.get("elo_band", c.get("elo_target", 1200)) - user_elo))
    return candidates


def get_calibration_challenges() -> list[dict[str, Any]]:
    """Return the 10 calibration challenges in order (cal-001 through cal-010)."""
    calibration = [
        c for c in get_all_challenges().values()
        if c.get("category") == "calibration"
    ]
    calibration.sort(key=lambda c: c["id"])
    return calibration
