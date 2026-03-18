"""Shared fixtures for CodeGambit backend tests."""

from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.database import Base, get_session
from app.main import app
from app.models.challenge import Challenge
from app.models.user import UserProfile

# In-memory SQLite for tests
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def override_get_session() -> AsyncGenerator[AsyncSession, None]:
    async with TestSessionLocal() as session:
        yield session


app.dependency_overrides[get_session] = override_get_session


@pytest.fixture(autouse=True)
async def setup_database():
    """Create all tables before each test and drop them after."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def session() -> AsyncGenerator[AsyncSession, None]:
    """Provide a test database session."""
    async with TestSessionLocal() as session:
        yield session


@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """Provide an async HTTP client bound to the FastAPI app."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
async def sample_user(session: AsyncSession) -> UserProfile:
    """Create and return a default test user."""
    user = UserProfile(
        id=1,
        display_name="TestDeveloper",
        elo_overall=1200,
        elo_architecture=1200,
        elo_framework_depth=1200,
        elo_complexity_mgmt=1200,
        total_submissions=0,
        challenges_completed=0,
        calibration_complete=False,
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


@pytest.fixture
async def sample_challenge(session: AsyncSession) -> Challenge:
    """Create and return a test challenge in the DB with complete rubric."""
    challenge = Challenge(
        id="test-challenge-001",
        title="Test Challenge",
        description="A test challenge for unit tests.",
        domain="langchain",
        difficulty="intermediate",
        mode="socratic",
        category="training",
        tags=["test", "unit"],
        starter_code="# starter code",
        rubric={
            "architecture": {"weight": 0.4, "description": "Solution architecture quality"},
            "framework_depth": {"weight": 0.3, "description": "Framework API usage depth"},
            "complexity_mgmt": {"weight": 0.3, "description": "Complexity management"},
        },
        constraints={"time_limit": "30m"},
        expected_concepts=["testing"],
        elo_target=1200,
        test_cases=[{"name": "basic", "code": "assert True"}],
        reference_solution="print('solution')",
    )
    session.add(challenge)
    await session.commit()
    await session.refresh(challenge)
    return challenge


@pytest.fixture
def mock_evaluator(monkeypatch):
    """Mock the ClaudeEvaluator to return deterministic scores."""
    from app.services.evaluator import EvaluationResult

    def mock_evaluation(mode: str) -> EvaluationResult:
        return EvaluationResult(
            overall_score=70,
            architecture_score=68,
            framework_depth_score=72,
            complexity_mgmt_score=66,
            feedback_summary=f"Mock evaluation ({mode} mode).",
            strengths=["Good structure"],
            improvements=["Add tests"],
            mode_specific_feedback=f"Mock {mode} feedback.",
            raw_ai_response={"mock": True},
            model_used="mock",
            tokens_used=0,
        )

    monkeypatch.setattr(
        "app.services.evaluator._mock_evaluation", mock_evaluation
    )


@pytest.fixture
async def calibration_challenges(session: AsyncSession) -> list[Challenge]:
    """Create calibration challenges spanning all ELO bands."""
    challenges = []
    bands = [800, 1000, 1200, 1400, 1600]
    for i, band in enumerate(bands):
        for j in range(2):
            idx = i * 2 + j + 1
            ch = Challenge(
                id=f"cal-{idx:03d}",
                title=f"Calibration Challenge {idx}",
                description=f"Calibration challenge for band {band}",
                domain="python",
                difficulty="intermediate",
                mode="socratic",
                category="calibration",
                tags=["calibration"],
                starter_code="# start",
                rubric={
                    "architecture": {"weight": 0.4},
                    "framework_depth": {"weight": 0.3},
                    "complexity_mgmt": {"weight": 0.3},
                },
                constraints={},
                expected_concepts=[],
                elo_target=band,
                test_cases=[{"name": "basic", "code": "assert True"}],
                reference_solution="pass",
            )
            session.add(ch)
            challenges.append(ch)
    await session.commit()
    return challenges
