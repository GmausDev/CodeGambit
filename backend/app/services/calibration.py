from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.challenge import Challenge
from app.models.user import UserProfile


class CalibrationService:
    """Calibration flow: 2 challenges per ELO band to estimate initial rating."""

    BANDS = [800, 1000, 1200, 1400, 1600]
    CHALLENGES_PER_BAND = 2
    TOTAL_CHALLENGES = len(BANDS) * CHALLENGES_PER_BAND  # 10

    async def _get_user(self, session: AsyncSession, user_id: int) -> UserProfile:
        result = await session.execute(
            select(UserProfile).where(UserProfile.id == user_id)
        )
        user = result.scalar_one_or_none()
        if user is None:
            raise ValueError(f"User {user_id} not found")
        return user

    async def _find_challenge_for_band(
        self, session: AsyncSession, target_elo: int
    ) -> Challenge | None:
        """Find a challenge closest to the target ELO band."""
        margin = 150
        stmt = (
            select(Challenge)
            .where(Challenge.elo_target.between(target_elo - margin, target_elo + margin))
            .order_by(func.abs(Challenge.elo_target - target_elo))
            .limit(1)
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    def _current_band_index(self, calibration_step: int) -> int:
        """Which band the user is currently in based on step number."""
        return min(calibration_step // self.CHALLENGES_PER_BAND, len(self.BANDS) - 1)

    async def start_calibration(self, session: AsyncSession, user_id: int) -> dict:
        """Reset calibration state and return first challenge info."""
        user = await self._get_user(session, user_id)
        user.calibration_complete = False
        user.elo_overall = 1200
        user.elo_architecture = 1200
        user.elo_framework_depth = 1200
        user.elo_complexity_mgmt = 1200
        session.add(user)
        await session.flush()

        return await self._get_challenge_for_step(session, 0)

    async def get_next_challenge(
        self, session: AsyncSession, user_id: int, calibration_step: int
    ) -> dict:
        """Based on calibration progress, return the next challenge."""
        user = await self._get_user(session, user_id)

        if user.calibration_complete:
            return {
                "status": "already_complete",
                "message": "Calibration already finished.",
            }

        if calibration_step >= self.TOTAL_CHALLENGES:
            return await self.complete_calibration(session, user_id)

        return await self._get_challenge_for_step(session, calibration_step)

    async def _get_challenge_for_step(
        self, session: AsyncSession, step: int
    ) -> dict:
        """Return challenge info for a given calibration step."""
        band_idx = self._current_band_index(step)
        target_elo = self.BANDS[band_idx]

        challenge = await self._find_challenge_for_band(session, target_elo)
        if challenge is None:
            return {
                "status": "no_challenge",
                "message": f"No challenge available for ELO band {target_elo}",
                "calibration_step": step,
                "total_steps": self.TOTAL_CHALLENGES,
                "target_elo": target_elo,
            }

        return {
            "status": "challenge_ready",
            "calibration_step": step,
            "total_steps": self.TOTAL_CHALLENGES,
            "band": target_elo,
            "challenge_id": challenge.id,
            "challenge_title": challenge.title,
            "challenge_difficulty": challenge.difficulty,
        }

    async def complete_calibration(
        self, session: AsyncSession, user_id: int
    ) -> dict:
        """Mark calibration as complete and return final ELO ratings."""
        user = await self._get_user(session, user_id)
        user.calibration_complete = True
        session.add(user)
        await session.flush()

        return {
            "status": "calibration_complete",
            "elo_overall": user.elo_overall,
            "elo_architecture": user.elo_architecture,
            "elo_framework_depth": user.elo_framework_depth,
            "elo_complexity_mgmt": user.elo_complexity_mgmt,
        }
