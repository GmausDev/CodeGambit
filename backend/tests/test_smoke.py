"""Smoke test: full submission pipeline end-to-end."""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.challenge import Challenge
from app.models.submission import Submission
from app.models.user import UserProfile
from app.api.submissions import run_evaluation_pipeline
from tests.conftest import TestSessionLocal


class TestSubmissionPipeline:
    async def test_full_pipeline(
        self,
        client: AsyncClient,
        session: AsyncSession,
        sample_challenge: Challenge,
        sample_user: UserProfile,
        mock_evaluator,
        monkeypatch,
    ):
        """Full pipeline: create submission -> run pipeline -> GET result -> verify evaluation."""
        # Patch async_session used by the pipeline to use our test DB
        monkeypatch.setattr("app.api.submissions.async_session", TestSessionLocal)

        # 1. Create submission directly in DB (avoids double pipeline from BackgroundTasks)
        sub = Submission(
            challenge_id=sample_challenge.id,
            code="print('hello world')",
            mode="adversarial",
            status="pending",
        )
        session.add(sub)
        await session.commit()
        await session.refresh(sub)
        submission_id = sub.id

        # 2. Run the evaluation pipeline directly
        await run_evaluation_pipeline(submission_id)

        # 3. GET the submission via API and verify evaluation is populated
        resp = await client.get(f"/api/submissions/{submission_id}")
        assert resp.status_code == 200
        data = resp.json()

        assert data["submission"]["status"] == "completed"
        assert data["evaluation"] is not None
        assert data["evaluation"]["overall_score"] >= 0
        assert data["evaluation"]["architecture_score"] >= 0
        assert data["evaluation"]["framework_depth_score"] >= 0
        assert data["evaluation"]["complexity_mgmt_score"] >= 0
        assert len(data["evaluation"]["feedback_summary"]) > 0

    async def test_health_endpoint(self, client: AsyncClient):
        """GET /api/health returns ok status."""
        resp = await client.get("/api/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert data["version"] == "0.1.0"
