from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.elo_history import ELOHistory
from app.models.user import UserProfile


class ELOService:
    DIMENSIONS = ["overall", "architecture", "framework_depth", "complexity_mgmt"]

    # Maps dimension names to Evaluation model score fields
    DIMENSION_SCORE_FIELDS = {
        "overall": "overall_score",
        "architecture": "architecture_score",
        "framework_depth": "framework_depth_score",
        "complexity_mgmt": "complexity_mgmt_score",
    }

    # Maps dimension names to UserProfile ELO fields
    DIMENSION_ELO_FIELDS = {
        "overall": "elo_overall",
        "architecture": "elo_architecture",
        "framework_depth": "elo_framework_depth",
        "complexity_mgmt": "elo_complexity_mgmt",
    }

    def get_k_factor(self, user: UserProfile) -> int:
        """Dynamic K-factor: higher during calibration for faster convergence."""
        if not user.calibration_complete:
            return 40
        if user.total_submissions < 10:
            return 32
        if user.total_submissions < 25:
            return 24
        return 16

    def calculate_expected(self, player_elo: int, challenge_elo: int) -> float:
        """Standard ELO expected score: probability of player winning."""
        return 1.0 / (1.0 + 10 ** ((challenge_elo - player_elo) / 400))

    def calculate_actual_score(self, test_pass_rate: float, ai_scores: dict) -> dict:
        """Blend test results with AI evaluation per dimension.

        Each dimension score = 30% test_pass_rate + 70% AI score (normalized 0-1).
        ai_scores should be a dict of dimension -> int (0-100 from Evaluation).
        """
        result = {}
        for dim in self.DIMENSIONS:
            ai_raw = ai_scores.get(dim, 50)
            ai_normalized = max(0.0, min(1.0, ai_raw / 100.0))
            actual = 0.3 * test_pass_rate + 0.7 * ai_normalized
            result[dim] = round(actual, 4)
        return result

    async def update_elo(
        self,
        session: AsyncSession,
        user: UserProfile,
        submission_id: int,
        challenge_elo: int,
        test_pass_rate: float,
        ai_scores: dict,
    ) -> dict:
        """Calculate and apply ELO updates for all 4 dimensions.

        Returns {dimension: {before, after, delta}} for each dimension.
        """
        k = self.get_k_factor(user)
        actual_scores = self.calculate_actual_score(test_pass_rate, ai_scores)
        changes = {}

        for dim in self.DIMENSIONS:
            elo_field = self.DIMENSION_ELO_FIELDS[dim]
            current_elo = getattr(user, elo_field)
            expected = self.calculate_expected(current_elo, challenge_elo)
            actual = actual_scores[dim]
            delta = round(k * (actual - expected))
            new_elo = max(100, current_elo + delta)  # Floor at 100

            setattr(user, elo_field, new_elo)

            history = ELOHistory(
                submission_id=submission_id,
                dimension=dim,
                elo_before=current_elo,
                elo_after=new_elo,
                delta=new_elo - current_elo,
            )
            session.add(history)

            changes[dim] = {
                "before": current_elo,
                "after": new_elo,
                "delta": new_elo - current_elo,
            }

        user.total_submissions += 1
        session.add(user)
        await session.flush()

        return changes

    async def get_history(
        self,
        session: AsyncSession,
        dimension: str | None = None,
    ) -> list[ELOHistory]:
        """Retrieve ELO history, optionally filtered by dimension."""
        stmt = select(ELOHistory).order_by(ELOHistory.created_at.desc())
        if dimension and dimension in self.DIMENSIONS:
            stmt = stmt.where(ELOHistory.dimension == dimension)
        result = await session.execute(stmt)
        return list(result.scalars().all())
