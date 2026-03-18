from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.health import router as health_router
from app.api.challenges import router as challenges_router
from app.api.submissions import router as submissions_router
from app.api.users import router as users_router
from app.config import settings
from app.database import init_db
from app.services.challenge_loader import load_challenges


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    load_challenges()
    yield


app = FastAPI(title="CodeGambit API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router, prefix="/api")
app.include_router(challenges_router, prefix="/api")
app.include_router(submissions_router, prefix="/api")
app.include_router(users_router)
