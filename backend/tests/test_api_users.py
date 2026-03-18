"""Integration tests for the user API endpoints."""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import UserProfile


class TestGetProfile:
    async def test_get_profile_200(
        self, client: AsyncClient, sample_user: UserProfile
    ):
        """GET /api/user/profile returns 200 with user data."""
        resp = await client.get("/api/user/profile")
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == 1
        assert data["display_name"] == "TestDeveloper"
        assert data["elo_overall"] == 1200
        assert data["calibration_complete"] is False


class TestGetEloHistory:
    async def test_get_elo_history_200(
        self, client: AsyncClient, sample_user: UserProfile
    ):
        """GET /api/user/elo-history returns 200 with empty list initially."""
        resp = await client.get("/api/user/elo-history")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) == 0

    async def test_get_elo_history_with_dimension(
        self, client: AsyncClient, sample_user: UserProfile
    ):
        """GET /api/user/elo-history?dimension=overall returns 200."""
        resp = await client.get(
            "/api/user/elo-history", params={"dimension": "overall"}
        )
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)


class TestGetStats:
    async def test_get_stats_200(
        self, client: AsyncClient, sample_user: UserProfile
    ):
        """GET /api/user/stats returns 200 with aggregated stats."""
        resp = await client.get("/api/user/stats")
        assert resp.status_code == 200
        data = resp.json()
        assert "total_submissions" in data
        assert "challenges_completed" in data
        assert "completion_rate" in data
        assert "calibration_complete" in data
        assert "elo_average" in data
        assert "elo_min" in data
        assert "elo_max" in data
        assert "elo_breakdown" in data
        assert data["elo_average"] == 1200
        assert data["elo_breakdown"]["overall"] == 1200
