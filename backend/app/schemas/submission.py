from datetime import datetime

from pydantic import BaseModel, ConfigDict


class SubmissionCreate(BaseModel):
    challenge_id: str
    code: str
    mode: str


class SubmissionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    challenge_id: str
    code: str
    mode: str
    status: str
    sandbox_stdout: str | None = None
    sandbox_stderr: str | None = None
    sandbox_exit_code: int | None = None
    execution_time_ms: int | None = None
    created_at: datetime
