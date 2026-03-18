from datetime import datetime

from pydantic import BaseModel, ConfigDict


class EvaluationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    submission_id: int
    overall_score: int
    architecture_score: int
    framework_depth_score: int
    complexity_mgmt_score: int
    feedback_summary: str
    strengths: list[str] = []
    improvements: list[str] = []
    mode_specific_feedback: str | None = None
    raw_ai_response: dict | None = None
    model_used: str | None = None
    tokens_used: int | None = None
    created_at: datetime
