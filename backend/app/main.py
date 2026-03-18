import time
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware

from app.api.challenges import router as challenges_router
from app.api.health import router as health_router
from app.api.submissions import router as submissions_router
from app.api.users import router as users_router
from app.config import settings
from app.database import engine, init_db
from app.services.challenge_loader import load_challenges, sync_challenges_to_db

_submission_cooldowns: dict[str, float] = {}
SUBMISSION_COOLDOWN_SECONDS = 5


async def check_submission_rate(request: Request):
    client_ip = request.client.host if request.client else "unknown"
    now = time.monotonic()
    last = _submission_cooldowns.get(client_ip, 0)
    if now - last < SUBMISSION_COOLDOWN_SECONDS:
        raise HTTPException(429, "Please wait before submitting again")
    _submission_cooldowns[client_ip] = now


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    load_challenges()
    await sync_challenges_to_db(engine)
    yield


app = FastAPI(title="CodeGambit API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS.split(","),
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)

app.include_router(health_router, prefix="/api")
app.include_router(challenges_router, prefix="/api")
app.include_router(
    submissions_router,
    prefix="/api",
    dependencies=[Depends(check_submission_rate)],
)
app.include_router(users_router, prefix="/api/user")
