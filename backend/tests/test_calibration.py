"""Tests for the calibration service."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.challenge import Challenge
from app.models.user import UserProfile
from app.services.calibration import CalibrationService


class TestBandCalculation:
    """Test _current_band_index mapping from step to ELO band."""

    def setup_method(self):
        self.svc = CalibrationService()

    def test_steps_0_1_map_to_band_800(self):
        assert self.svc._current_band_index(0) == 0
        assert self.svc._current_band_index(1) == 0
        assert self.svc.BANDS[self.svc._current_band_index(0)] == 800

    def test_steps_2_3_map_to_band_1000(self):
        assert self.svc._current_band_index(2) == 1
        assert self.svc._current_band_index(3) == 1
        assert self.svc.BANDS[self.svc._current_band_index(2)] == 1000

    def test_steps_4_5_map_to_band_1200(self):
        assert self.svc._current_band_index(4) == 2
        assert self.svc._current_band_index(5) == 2
        assert self.svc.BANDS[self.svc._current_band_index(4)] == 1200

    def test_steps_6_7_map_to_band_1400(self):
        assert self.svc._current_band_index(6) == 3
        assert self.svc._current_band_index(7) == 3
        assert self.svc.BANDS[self.svc._current_band_index(6)] == 1400

    def test_steps_8_9_map_to_band_1600(self):
        assert self.svc._current_band_index(8) == 4
        assert self.svc._current_band_index(9) == 4
        assert self.svc.BANDS[self.svc._current_band_index(8)] == 1600

    def test_overflow_step_clamped_to_last_band(self):
        assert self.svc._current_band_index(100) == 4

    def test_total_challenges_is_10(self):
        assert self.svc.TOTAL_CHALLENGES == 10


class TestStartCalibration:
    async def test_resets_user_state(
        self, session: AsyncSession, sample_user: UserProfile
    ):
        # Modify user to non-default values
        sample_user.elo_overall = 1500
        sample_user.calibration_complete = True
        session.add(sample_user)
        await session.flush()

        svc = CalibrationService()
        result = await svc.start_calibration(session, sample_user.id)

        await session.refresh(sample_user)
        assert sample_user.calibration_complete is False
        assert sample_user.elo_overall == 1200
        assert sample_user.elo_architecture == 1200
        assert sample_user.elo_framework_depth == 1200
        assert sample_user.elo_complexity_mgmt == 1200

    async def test_returns_first_challenge_info(
        self,
        session: AsyncSession,
        sample_user: UserProfile,
        calibration_challenges: list[Challenge],
    ):
        svc = CalibrationService()
        result = await svc.start_calibration(session, sample_user.id)
        assert result["calibration_step"] == 0
        assert result["total_steps"] == 10

    async def test_nonexistent_user_raises(self, session: AsyncSession):
        svc = CalibrationService()
        with pytest.raises(ValueError, match="User 9999 not found"):
            await svc.start_calibration(session, 9999)


class TestGetNextChallenge:
    async def test_already_complete(
        self, session: AsyncSession, sample_user: UserProfile
    ):
        sample_user.calibration_complete = True
        session.add(sample_user)
        await session.flush()

        svc = CalibrationService()
        result = await svc.get_next_challenge(session, sample_user.id, 0)
        assert result["status"] == "already_complete"

    async def test_returns_challenge_for_step(
        self,
        session: AsyncSession,
        sample_user: UserProfile,
        calibration_challenges: list[Challenge],
    ):
        svc = CalibrationService()
        result = await svc.get_next_challenge(session, sample_user.id, 3)
        assert result["status"] == "challenge_ready"
        assert result["band"] == 1000  # steps 2-3 -> band index 1 -> 1000

    async def test_step_past_total_completes_calibration(
        self, session: AsyncSession, sample_user: UserProfile
    ):
        svc = CalibrationService()
        result = await svc.get_next_challenge(session, sample_user.id, 10)
        assert result["status"] == "calibration_complete"


class TestCompleteCalibration:
    async def test_sets_calibration_complete(
        self, session: AsyncSession, sample_user: UserProfile
    ):
        svc = CalibrationService()
        result = await svc.complete_calibration(session, sample_user.id)

        await session.refresh(sample_user)
        assert sample_user.calibration_complete is True
        assert result["status"] == "calibration_complete"
        assert "elo_overall" in result
