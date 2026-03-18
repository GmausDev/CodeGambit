from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ChallengeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    description: str
    domain: str
    difficulty: str
    mode: str
    category: str
    tags: list[str] = []
    starter_code: str | None = None
    rubric: dict = {}
    constraints: dict = {}
    expected_concepts: list[str] = []
    elo_target: int = 1200
    test_cases: list[dict] = []
    reference_solution: str | None = None
    created_at: datetime


class ChallengeList(BaseModel):
    challenges: list[ChallengeOut]
    total: int
