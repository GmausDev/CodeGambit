"""Load and cache challenge definitions from YAML files."""

import logging
from pathlib import Path
from typing import Any

import yaml
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncEngine

logger = logging.getLogger(__name__)

# In-memory cache: challenge id -> challenge dict
_challenges: dict[str, dict[str, Any]] = {}

REQUIRED_FIELDS = {
    "id", "title", "description", "domain", "difficulty",
    "mode", "category", "tags", "rubric", "test_cases",
    "reference_solution",
}

CHALLENGES_DIR = Path(__file__).resolve().parents[3] / "challenges"


def _validate_challenge(data: dict[str, Any], filepath: Path) -> bool:
    """Validate that a challenge dict has all required fields."""
    missing = REQUIRED_FIELDS - set(data.keys())
    if missing:
        logger.warning("Challenge %s missing fields: %s", filepath, missing)
        return False
    if not isinstance(data.get("id"), str) or not data["id"]:
        logger.warning("Challenge %s has invalid id", filepath)
        return False
    return True


def load_challenges(directory: Path | None = None) -> dict[str, dict[str, Any]]:
    """Load all YAML challenge files from directory recursively.

    Returns the populated cache dict.
    """
    global _challenges
    root = directory or CHALLENGES_DIR
    _challenges.clear()

    if not root.is_dir():
        logger.error("Challenges directory not found: %s", root)
        return _challenges

    yaml_files = list(root.rglob("*.yaml")) + list(root.rglob("*.yml"))

    for filepath in yaml_files:
        try:
            with open(filepath) as f:
                data = yaml.safe_load(f)
        except Exception:
            logger.exception("Failed to parse YAML: %s", filepath)
            continue

        if not isinstance(data, dict):
            logger.warning("Skipping non-dict YAML: %s", filepath)
            continue

        if not _validate_challenge(data, filepath):
            continue

        challenge_id = data["id"]
        if challenge_id in _challenges:
            logger.warning("Duplicate challenge id '%s' in %s — skipping", challenge_id, filepath)
            continue

        _challenges[challenge_id] = data

    logger.info("Loaded %d challenges from %s", len(_challenges), root)
    return _challenges


def reload_challenges(directory: Path | None = None) -> dict[str, dict[str, Any]]:
    """Clear cache and reload all challenges."""
    return load_challenges(directory)


def get_all_challenges() -> dict[str, dict[str, Any]]:
    """Return the in-memory challenge cache."""
    return _challenges


def get_challenge_by_id(challenge_id: str) -> dict[str, Any] | None:
    """Return a single challenge by id, or None."""
    return _challenges.get(challenge_id)


async def sync_challenges_to_db(engine: AsyncEngine) -> int:
    """Upsert all cached challenges into the challenges DB table.

    Returns the number of challenges synced.
    """
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

    from app.models.challenge import Challenge

    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    synced = 0

    async with session_factory() as session:
        for cid, data in _challenges.items():
            result = await session.execute(
                select(Challenge).where(Challenge.id == cid)
            )
            existing = result.scalar_one_or_none()

            if existing:
                # Update existing challenge
                existing.title = data.get("title", existing.title)
                existing.description = data.get("description", existing.description)
                existing.domain = data.get("domain", existing.domain)
                existing.difficulty = data.get("difficulty", existing.difficulty)
                existing.mode = data.get("mode", existing.mode)
                existing.category = data.get("category", existing.category)
                existing.tags = data.get("tags", existing.tags)
                existing.starter_code = data.get("starter_code")
                existing.rubric = data.get("rubric", existing.rubric)
                existing.constraints = data.get("constraints", {})
                existing.expected_concepts = data.get("expected_concepts", [])
                existing.elo_target = data.get("elo_band", existing.elo_target)
                existing.test_cases = data.get("test_cases", existing.test_cases)
                existing.reference_solution = data.get("reference_solution")
            else:
                # Insert new challenge
                challenge = Challenge(
                    id=cid,
                    title=data["title"],
                    description=data["description"],
                    domain=data["domain"],
                    difficulty=data["difficulty"],
                    mode=data["mode"],
                    category=data["category"],
                    tags=data.get("tags", []),
                    starter_code=data.get("starter_code"),
                    rubric=data.get("rubric", {}),
                    constraints=data.get("constraints", {}),
                    expected_concepts=data.get("expected_concepts", []),
                    elo_target=data.get("elo_band", 1200),
                    test_cases=data.get("test_cases", []),
                    reference_solution=data.get("reference_solution"),
                )
                session.add(challenge)

            synced += 1

        await session.commit()

    logger.info("Synced %d challenges to database", synced)
    return synced
