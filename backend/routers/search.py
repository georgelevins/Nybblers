"""
Search router — semantic vector search + analytics endpoints.
All routes embed the query via OpenAI and search the Postgres pgvector index.
Falls back to a 503 if the DB pool is not initialised (no DATABASE_URL set).
"""

from fastapi import APIRouter, HTTPException, Query

import database
from models import (
    GrowthMomentumResponse,
    MentionsTrendResponse,
    SearchRequest,
    SearchResponse,
    SubredditUsersResponse,
    TopMatchesResponse,
)
from repositories import posts as posts_repo

router = APIRouter()


def _require_pool():
    """Raise 503 if the DB pool is not available."""
    if database._pool is None:
        raise HTTPException(
            status_code=503,
            detail="Database not available. Check DATABASE_URL configuration.",
        )


@router.post("", response_model=SearchResponse)
async def search(request: SearchRequest) -> SearchResponse:
    """Semantic search for Reddit posts matching the query using pgvector cosine similarity."""
    _require_pool()
    try:
        return await posts_repo.search_posts(
            query_text=request.query,
            subreddit=request.subreddit,
            limit=request.limit,
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))


@router.get("/mentions-over-time", response_model=MentionsTrendResponse)
async def mentions_over_time(q: str = Query(..., description="Search query")) -> MentionsTrendResponse:
    """Monthly count of Reddit posts semantically matching the query."""
    _require_pool()
    try:
        return await posts_repo.get_mentions_over_time(q)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))


@router.get("/users-by-subreddit", response_model=SubredditUsersResponse)
async def users_by_subreddit(
    q: str = Query(..., description="Search query"),
    limit: int = Query(default=50, ge=1, le=200),
) -> SubredditUsersResponse:
    """Unique Reddit authors per subreddit from posts matching the query."""
    _require_pool()
    try:
        return await posts_repo.get_users_by_subreddit(q, limit=limit)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))


@router.get("/top-matches", response_model=TopMatchesResponse)
async def top_matches(
    q: str = Query(..., description="Search query"),
    limit: int = Query(default=10, ge=1, le=50),
) -> TopMatchesResponse:
    """Top semantically similar Reddit posts and comments for the query."""
    _require_pool()
    try:
        return await posts_repo.get_top_matches(q, limit=limit)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))


@router.get("/growth-momentum", response_model=GrowthMomentumResponse)
async def growth_momentum(q: str = Query(..., description="Search query")) -> GrowthMomentumResponse:
    """Weekly and monthly time series of post counts matching the query."""
    _require_pool()
    try:
        return await posts_repo.get_growth_data(q)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
