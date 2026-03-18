"""Integration tests for the submissions API endpoints."""

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.challenge import Challenge
from app.models.evaluation import Evaluation
from app.models.submission import Submission


class TestCreateSubmission:
    async def test_create_submission_201(
        self, client: AsyncClient, sample_challenge: Challenge
    ):
        """POST /api/submissions returns 201 with valid data."""
        resp = await client.post(
            "/api/submissions",
            json={
                "challenge_id": sample_challenge.id,
                "code": "print('hello world')",
                "mode": "socratic",
            },
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["challenge_id"] == sample_challenge.id
        assert data["code"] == "print('hello world')"
        assert data["mode"] == "socratic"
        assert data["status"] == "pending"
        assert "id" in data

    async def test_create_submission_404_challenge(self, client: AsyncClient):
        """POST /api/submissions returns 404 for nonexistent challenge."""
        resp = await client.post(
            "/api/submissions",
            json={
                "challenge_id": "nonexistent-challenge",
                "code": "print('test')",
                "mode": "socratic",
            },
        )
        assert resp.status_code == 404

    async def test_create_submission_400_invalid_mode(
        self, client: AsyncClient, sample_challenge: Challenge
    ):
        """POST /api/submissions returns 400 for invalid mode."""
        resp = await client.post(
            "/api/submissions",
            json={
                "challenge_id": sample_challenge.id,
                "code": "print('test')",
                "mode": "invalid_mode",
            },
        )
        assert resp.status_code == 400


class TestGetSubmission:
    async def test_get_submission_200(
        self, client: AsyncClient, session: AsyncSession, sample_challenge: Challenge
    ):
        """GET /api/submissions/{id} returns 200 for an existing submission."""
        sub = Submission(
            challenge_id=sample_challenge.id,
            code="print('test')",
            mode="adversarial",
            status="pending",
        )
        session.add(sub)
        await session.commit()
        await session.refresh(sub)

        resp = await client.get(f"/api/submissions/{sub.id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["submission"]["id"] == sub.id
        assert data["submission"]["challenge_id"] == sample_challenge.id
        assert data["evaluation"] is None

    async def test_get_submission_with_evaluation(
        self, client: AsyncClient, session: AsyncSession, sample_challenge: Challenge
    ):
        """GET /api/submissions/{id} includes evaluation when present."""
        sub = Submission(
            challenge_id=sample_challenge.id,
            code="print('test')",
            mode="adversarial",
            status="evaluated",
        )
        session.add(sub)
        await session.commit()
        await session.refresh(sub)

        evaluation = Evaluation(
            submission_id=sub.id,
            overall_score=75,
            architecture_score=70,
            framework_depth_score=72,
            complexity_mgmt_score=68,
            feedback_summary="Good work.",
            strengths=["Clean code"],
            improvements=["Add tests"],
        )
        session.add(evaluation)
        await session.commit()

        resp = await client.get(f"/api/submissions/{sub.id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["evaluation"] is not None
        assert data["evaluation"]["overall_score"] == 75

    async def test_get_submission_404(self, client: AsyncClient):
        """GET /api/submissions/{id} returns 404 for nonexistent submission."""
        resp = await client.get("/api/submissions/99999")
        assert resp.status_code == 404
