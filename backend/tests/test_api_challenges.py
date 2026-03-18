"""Integration tests for the challenges API endpoints."""

import pytest
from httpx import AsyncClient

from app.models.challenge import Challenge
from app.services.challenge_loader import load_challenges, get_all_challenges


@pytest.fixture(autouse=True)
async def _seed_challenges(session):
    """Load challenge YAML files into the in-memory cache for API tests."""
    load_challenges()


class TestListChallenges:
    async def test_list_challenges_200(self, client: AsyncClient):
        """GET /api/challenges returns 200 with a list."""
        resp = await client.get("/api/challenges")
        assert resp.status_code == 200
        data = resp.json()
        assert "challenges" in data
        assert "total" in data
        assert isinstance(data["challenges"], list)
        assert data["total"] >= 0

    async def test_list_excludes_reference_solution(self, client: AsyncClient):
        """Listed challenges should not include reference_solution."""
        resp = await client.get("/api/challenges")
        data = resp.json()
        if data["total"] > 0:
            assert "reference_solution" not in data["challenges"][0]

    async def test_list_filter_by_difficulty(self, client: AsyncClient):
        """Filtering by difficulty should return matching challenges or empty."""
        resp = await client.get("/api/challenges", params={"difficulty": "intermediate"})
        assert resp.status_code == 200
        data = resp.json()
        for c in data["challenges"]:
            assert c["difficulty"] == "intermediate"


class TestGetChallenge:
    async def test_get_challenge_200(self, client: AsyncClient):
        """GET /api/challenges/{id} returns 200 for a known challenge."""
        all_ch = get_all_challenges()
        if not all_ch:
            pytest.skip("No challenges loaded")
        challenge_id = next(iter(all_ch))
        resp = await client.get(f"/api/challenges/{challenge_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == challenge_id
        assert "reference_solution" not in data

    async def test_get_challenge_404(self, client: AsyncClient):
        """GET /api/challenges/{id} returns 404 for a missing challenge."""
        resp = await client.get("/api/challenges/nonexistent-999")
        assert resp.status_code == 404


class TestGetReferenceSolution:
    async def test_get_reference_solution(self, client: AsyncClient):
        """GET /api/challenges/{id}/reference-solution returns the solution."""
        all_ch = get_all_challenges()
        if not all_ch:
            pytest.skip("No challenges loaded")
        challenge_id = next(iter(all_ch))
        resp = await client.get(f"/api/challenges/{challenge_id}/reference-solution")
        assert resp.status_code == 200
        data = resp.json()
        assert "challenge_id" in data
        assert "reference_solution" in data

    async def test_reference_solution_404(self, client: AsyncClient):
        """Reference solution for missing challenge returns 404."""
        resp = await client.get("/api/challenges/nonexistent-999/reference-solution")
        assert resp.status_code == 404
