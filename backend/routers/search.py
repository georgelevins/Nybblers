"""
Search router — semantic vector search + analytics endpoints.
All routes embed the query via OpenAI and search the Postgres pgvector index.
Falls back to a 503 if the DB pool is not initialised (no DATABASE_URL set).
"""

import asyncio
import time
from collections import OrderedDict

from fastapi import APIRouter, HTTPException, Query

import database
from models import (
    ActiveThreadsResponse,
    AnalyticsResponse,
    GrowthMomentumResponse,
    MentionsTrendResponse,
    SearchRequest,
    SearchResponse,
    SubredditUsersResponse,
    TopMatchesResponse,
)
from repositories import posts as posts_repo
from repositories.embeddings import embed_text

router = APIRouter()

# ── Response-level TTL cache for /analytics ───────────────────────────────────
_ANALYTICS_TTL = 1800  # seconds — 30 minutes (demo-friendly)
_ANALYTICS_MAX = 512

_analytics_cache: OrderedDict[str, tuple[float, AnalyticsResponse]] = OrderedDict()


def _analytics_cache_get(key: str) -> AnalyticsResponse | None:
    entry = _analytics_cache.get(key)
    if entry is None:
        return None
    ts, value = entry
    if time.monotonic() - ts > _ANALYTICS_TTL:
        del _analytics_cache[key]
        return None
    _analytics_cache.move_to_end(key)
    return value


def _analytics_cache_set(key: str, value: AnalyticsResponse) -> None:
    _analytics_cache[key] = (time.monotonic(), value)
    _analytics_cache.move_to_end(key)
    if len(_analytics_cache) > _ANALYTICS_MAX:
        _analytics_cache.popitem(last=False)


# ── Response-level TTL cache for /search ──────────────────────────────────────
_SEARCH_TTL = 1800  # seconds — 30 minutes
_SEARCH_MAX = 512

_search_cache: OrderedDict[str, tuple[float, object]] = OrderedDict()


def _search_cache_get(key: str) -> object | None:
    entry = _search_cache.get(key)
    if entry is None:
        return None
    ts, value = entry
    if time.monotonic() - ts > _SEARCH_TTL:
        del _search_cache[key]
        return None
    _search_cache.move_to_end(key)
    return value


def _search_cache_set(key: str, value: object) -> None:
    _search_cache[key] = (time.monotonic(), value)
    _search_cache.move_to_end(key)
    if len(_search_cache) > _SEARCH_MAX:
        _search_cache.popitem(last=False)


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

    cache_key = f"{request.query.strip().lower()}|{request.subreddit or ''}|{request.limit}"
    cached = _search_cache_get(cache_key)
    if cached is not None:
        return cached  # type: ignore[return-value]

    try:
        result = await posts_repo.search_posts(
            query_text=request.query,
            subreddit=request.subreddit,
            limit=request.limit,
        )
        _search_cache_set(cache_key, result)
        return result
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


@router.get("/active-threads", response_model=ActiveThreadsResponse)
async def active_threads(
    q: str = Query(..., description="Search query"),
    window_hours: int = Query(default=24, ge=1, le=720, description="Activity window in hours"),
    min_comments: int = Query(default=3, ge=1, description="Minimum comments within the window"),
    limit: int = Query(default=20, ge=1, le=50),
) -> ActiveThreadsResponse:
    """
    Semantically relevant posts with recent comment velocity.
    'Active' = at least min_comments posted in the window_hours before the thread's last activity.
    """
    _require_pool()
    try:
        return await posts_repo.get_active_threads(
            query_text=q,
            window_hours=window_hours,
            min_comments=min_comments,
            limit=limit,
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))


@router.get("/analytics", response_model=AnalyticsResponse)
async def analytics(
    q: str = Query(..., description="Search query"),
    top_matches_limit: int = Query(default=10, ge=1, le=50),
) -> AnalyticsResponse:
    """
    Combined analytics endpoint — embeds the query ONCE then runs all four
    analytics queries in parallel. Up to 4× faster than calling each endpoint
    individually. Results are cached for 5 minutes per unique query.
    """
    _require_pool()

    cache_key = f"{q.strip().lower()}|{top_matches_limit}"
    cached = _analytics_cache_get(cache_key)
    if cached is not None:
        return cached

    try:
        embedding = await embed_text(q.strip())

        mentions, subreddits, top_matches, growth = await asyncio.gather(
            posts_repo.get_mentions_over_time(q, embedding=embedding),
            posts_repo.get_users_by_subreddit(q, embedding=embedding),
            posts_repo.get_top_matches(q, limit=top_matches_limit, embedding=embedding),
            posts_repo.get_growth_data(q, embedding=embedding),
        )

        result = AnalyticsResponse(
            mentions=mentions,
            subreddits=subreddits,
            top_matches=top_matches,
            growth=growth,
        )
        _analytics_cache_set(cache_key, result)
        return result
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
