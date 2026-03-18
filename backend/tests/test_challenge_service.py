"""Tests for the challenge service."""

from unittest.mock import patch

import pytest

from app.services.challenge_service import (
    get_calibration_challenges,
    get_challenges,
    get_recommendations,
)

# Sample challenge data used across tests
SAMPLE_CHALLENGES = {
    "ch-001": {
        "id": "ch-001",
        "title": "Easy Socratic",
        "difficulty": "beginner",
        "mode": "socratic",
        "domain": "langchain",
        "category": "training",
        "elo_band": 900,
    },
    "ch-002": {
        "id": "ch-002",
        "title": "Intermediate Adversarial",
        "difficulty": "intermediate",
        "mode": "adversarial",
        "domain": "fastapi",
        "category": "training",
        "elo_band": 1200,
    },
    "ch-003": {
        "id": "ch-003",
        "title": "Advanced Socratic",
        "difficulty": "advanced",
        "mode": "socratic",
        "domain": "langchain",
        "category": "training",
        "elo_band": 1500,
    },
    "cal-001": {
        "id": "cal-001",
        "title": "Calibration 1",
        "difficulty": "beginner",
        "mode": "socratic",
        "domain": "python",
        "category": "calibration",
        "elo_band": 800,
    },
    "cal-002": {
        "id": "cal-002",
        "title": "Calibration 2",
        "difficulty": "intermediate",
        "mode": "socratic",
        "domain": "python",
        "category": "calibration",
        "elo_band": 1000,
    },
}


@pytest.fixture(autouse=True)
def mock_challenge_cache():
    """Patch the challenge loader cache with sample data."""
    with patch(
        "app.services.challenge_service.get_all_challenges",
        return_value=SAMPLE_CHALLENGES,
    ):
        yield


class TestGetChallenges:
    def test_returns_all(self):
        result = get_challenges()
        assert len(result) == 5

    def test_filter_by_difficulty(self):
        result = get_challenges(difficulty="intermediate")
        assert len(result) == 2
        assert all(c["difficulty"] == "intermediate" for c in result)

    def test_filter_by_mode(self):
        result = get_challenges(mode="socratic")
        assert len(result) == 4
        assert all(c["mode"] == "socratic" for c in result)

    def test_filter_by_domain(self):
        result = get_challenges(domain="langchain")
        assert len(result) == 2
        assert all(c["domain"] == "langchain" for c in result)

    def test_filter_combined(self):
        result = get_challenges(difficulty="beginner", mode="socratic")
        assert len(result) == 2  # ch-001 + cal-001

    def test_no_match_returns_empty(self):
        result = get_challenges(difficulty="nonexistent")
        assert result == []


class TestGetRecommendations:
    def test_elo_1200_returns_nearby(self):
        result = get_recommendations(user_elo=1200, completed_ids=[])
        elo_values = [c.get("elo_band", 1200) for c in result]
        assert all(1000 <= e <= 1400 for e in elo_values)

    def test_excludes_completed(self):
        result = get_recommendations(user_elo=1200, completed_ids=["ch-002"])
        ids = [c["id"] for c in result]
        assert "ch-002" not in ids

    def test_sorted_by_proximity(self):
        result = get_recommendations(user_elo=1200, completed_ids=[])
        if len(result) > 1:
            distances = [
                abs(c.get("elo_band", 1200) - 1200) for c in result
            ]
            assert distances == sorted(distances)

    def test_far_elo_returns_empty(self):
        result = get_recommendations(user_elo=2000, completed_ids=[])
        assert result == []


class TestGetCalibrationChallenges:
    def test_returns_only_calibration(self):
        result = get_calibration_challenges()
        assert len(result) == 2
        assert all(c["category"] == "calibration" for c in result)

    def test_sorted_by_id(self):
        result = get_calibration_challenges()
        ids = [c["id"] for c in result]
        assert ids == sorted(ids)
