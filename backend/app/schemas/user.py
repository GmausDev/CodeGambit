from datetime import datetime

from pydantic import BaseModel, ConfigDict


class UserProfileOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    display_name: str
    elo_overall: int
    elo_architecture: int
    elo_framework_depth: int
    elo_complexity_mgmt: int
    total_submissions: int
    challenges_completed: int
    calibration_complete: bool
    created_at: datetime
    updated_at: datetime


class ELOHistoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    submission_id: int
    dimension: str
    elo_before: int
    elo_after: int
    delta: int
    created_at: datetime


class HealthResponse(BaseModel):
    status: str
    version: str
