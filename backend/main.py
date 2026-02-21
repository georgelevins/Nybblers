"""
RedditDemand API — FastAPI backend for demand intelligence from Reddit.
"""

# Load .env BEFORE any other imports so module-level env reads (e.g. EMBEDDING_BACKEND) pick it up.
from pathlib import Path
from dotenv import load_dotenv

_env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=_env_path)
load_dotenv()  # fallback: .env in current working directory

from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import close_pool, get_pool, init_pool
from models import DatabaseHealthResponse, HealthResponse
from routers import alerts, search, threads, agent


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage app lifecycle: init DB pool on startup, close on shutdown."""
    await init_pool()
    yield
    await close_pool()


app = FastAPI(
    title="RedditDemand API",
    description="Demand intelligence platform — search Reddit for evidence that real people want the problem your business solves.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(search.router, prefix="/search", tags=["search"])
app.include_router(threads.router, prefix="/threads", tags=["threads"])
app.include_router(alerts.router, prefix="/alerts", tags=["alerts"])
app.include_router(agent.router, prefix="/agent", tags=["agent"])


@app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    """Health check endpoint."""
    return HealthResponse(status="ok", timestamp=datetime.utcnow())


@app.get("/health/db", response_model=DatabaseHealthResponse)
async def health_db() -> DatabaseHealthResponse:
    """Check if the app can connect to the database (e.g. SELECT 1)."""
    try:
        pool = await get_pool()
    except RuntimeError:
        return DatabaseHealthResponse(
            database="unavailable",
            detail="Database pool not initialized (missing or invalid DATABASE_URL).",
        )
    try:
        async with pool.acquire() as conn:
            await conn.fetchval("SELECT 1")
        return DatabaseHealthResponse(database="ok")
    except Exception as e:  # noqa: BLE001
        return DatabaseHealthResponse(
            database="unavailable",
            detail=str(e),
        )
