"""
RedditDemand API — FastAPI backend for demand intelligence from Reddit.
"""

from contextlib import asynccontextmanager
from datetime import datetime

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import close_pool, init_pool
from models import HealthResponse
from routers import alerts, search, threads, agent

load_dotenv()


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
