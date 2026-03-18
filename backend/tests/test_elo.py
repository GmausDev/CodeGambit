"""Unit tests for the ELO service."""


from app.models.user import UserProfile
from app.services.elo import ELOService

elo = ELOService()


def _make_user(**kwargs) -> UserProfile:
    """Create a UserProfile with sensible defaults, overridable via kwargs."""
    defaults = dict(
        id=1,
        display_name="Test",
        elo_overall=1200,
        elo_architecture=1200,
        elo_framework_depth=1200,
        elo_complexity_mgmt=1200,
        total_submissions=0,
        challenges_completed=0,
        calibration_complete=False,
    )
    defaults.update(kwargs)
    return UserProfile(**defaults)


class TestCalculateExpected:
    def test_equal_elo(self):
        """When both ELOs are equal, expected score should be ~0.5."""
        result = elo.calculate_expected(1200, 1200)
        assert abs(result - 0.5) < 0.01

    def test_higher_player(self):
        """Player with higher ELO should have expected > 0.5."""
        result = elo.calculate_expected(1600, 1200)
        assert result > 0.5

    def test_lower_player(self):
        """Player with lower ELO should have expected < 0.5."""
        result = elo.calculate_expected(800, 1200)
        assert result < 0.5

    def test_symmetry(self):
        """E(A vs B) + E(B vs A) should equal 1.0."""
        e1 = elo.calculate_expected(1400, 1000)
        e2 = elo.calculate_expected(1000, 1400)
        assert abs(e1 + e2 - 1.0) < 1e-9


class TestGetKFactor:
    def test_calibration_phase(self):
        """During calibration, K should be 40."""
        user = _make_user(calibration_complete=False, total_submissions=0)
        assert elo.get_k_factor(user) == 40

    def test_early_submissions(self):
        """With < 10 submissions post-calibration, K should be 32."""
        user = _make_user(calibration_complete=True, total_submissions=5)
        assert elo.get_k_factor(user) == 32

    def test_mid_submissions(self):
        """With 10-24 submissions post-calibration, K should be 24."""
        user = _make_user(calibration_complete=True, total_submissions=15)
        assert elo.get_k_factor(user) == 24

    def test_stable(self):
        """With >= 25 submissions post-calibration, K should be 16."""
        user = _make_user(calibration_complete=True, total_submissions=30)
        assert elo.get_k_factor(user) == 16


class TestCalculateActualScore:
    def test_blended_score(self):
        """Actual score = 0.3 * test_pass_rate + 0.7 * ai_score_normalized."""
        ai_scores = {
            "overall": 80,
            "architecture": 80,
            "framework_depth": 80,
            "complexity_mgmt": 80,
        }
        result = elo.calculate_actual_score(1.0, ai_scores)
        # 0.3 * 1.0 + 0.7 * 0.8 = 0.86
        for dim in ELOService.DIMENSIONS:
            assert abs(result[dim] - 0.86) < 0.01

    def test_zero_scores(self):
        """With zero test and AI scores, actual should be 0."""
        ai_scores = {dim: 0 for dim in ELOService.DIMENSIONS}
        result = elo.calculate_actual_score(0.0, ai_scores)
        for dim in ELOService.DIMENSIONS:
            assert result[dim] == 0.0

    def test_missing_dimension_defaults(self):
        """Missing dimension in ai_scores should default to 50."""
        result = elo.calculate_actual_score(0.5, {})
        # 0.3 * 0.5 + 0.7 * 0.5 = 0.5
        for dim in ELOService.DIMENSIONS:
            assert abs(result[dim] - 0.5) < 0.01

    def test_clamping(self):
        """AI scores above 100 should be clamped to 1.0."""
        ai_scores = {dim: 150 for dim in ELOService.DIMENSIONS}
        result = elo.calculate_actual_score(1.0, ai_scores)
        # 0.3 * 1.0 + 0.7 * 1.0 = 1.0
        for dim in ELOService.DIMENSIONS:
            assert abs(result[dim] - 1.0) < 0.01


class TestUpdateElo:
    async def test_update_elo_changes_rating(self, session, sample_user, sample_challenge):
        """Updating ELO should change the user's rating and create history records."""
        from app.models.submission import Submission

        sub = Submission(
            challenge_id=sample_challenge.id,
            code="print('test')",
            mode="socratic",
            status="evaluated",
        )
        session.add(sub)
        await session.commit()
        await session.refresh(sub)

        ai_scores = {dim: 70 for dim in ELOService.DIMENSIONS}
        changes = await elo.update_elo(
            session=session,
            user=sample_user,
            submission_id=sub.id,
            challenge_elo=1200,
            test_pass_rate=0.8,
            ai_scores=ai_scores,
        )

        assert len(changes) == 4
        for dim in ELOService.DIMENSIONS:
            assert "before" in changes[dim]
            assert "after" in changes[dim]
            assert "delta" in changes[dim]
