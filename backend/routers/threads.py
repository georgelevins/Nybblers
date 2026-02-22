"""
Threads router — post detail and opportunities.
"""

from fastapi import APIRouter, HTTPException, Query

import database
from database import get_pool
from models import ActiveThreadsResponse, OpportunitiesResponse, OpportunityPost, ThreadDetail
from repositories import posts as posts_repo

router = APIRouter()


def _require_pool():
    if database._pool is None:
        raise HTTPException(
            status_code=503,
            detail="Database not available. Check DATABASE_URL configuration.",
        )


@router.get("/opportunities", response_model=OpportunitiesResponse)
async def get_opportunities(
    subreddit: str | None = None,
    limit: int = 20,
    min_activity_ratio: float = 0.0,
) -> OpportunitiesResponse:
    """
    Returns posts ordered by activity_ratio descending.
    High activity_ratio = more comments relative to post age.
    """
    _require_pool()
    pool = await get_pool()

    sql = """
        SELECT
            id, title, subreddit, created_utc,
            COALESCE(num_comments, 0) AS num_comments,
            COALESCE(activity_ratio, 0.0) AS activity_ratio,
            last_comment_utc,
            url,
            FALSE AS ranks_on_google
        FROM posts
        WHERE COALESCE(activity_ratio, 0.0) >= $1
        {subreddit_filter}
        ORDER BY activity_ratio DESC NULLS LAST
        LIMIT $2
    """
    params: list = [min_activity_ratio, limit]
    subreddit_filter = ""
    if subreddit:
        subreddit_filter = "AND subreddit = $3"
        params.append(subreddit)

    full_sql = sql.format(subreddit_filter=subreddit_filter)

    async with pool.acquire() as conn:
        rows = await conn.fetch(full_sql, *params)

    results = [
        OpportunityPost(
            id=r["id"],
            title=r["title"],
            subreddit=r["subreddit"],
            created_utc=r["created_utc"],
            num_comments=r["num_comments"],
            activity_ratio=float(r["activity_ratio"]),
            last_comment_utc=r["last_comment_utc"],
            url=r["url"],
            ranks_on_google=r["ranks_on_google"],
        )
        for r in rows
    ]
    return OpportunitiesResponse(results=results)


@router.get("/activity", response_model=ActiveThreadsResponse)
async def threads_activity(
    ids: str = Query(..., description="Comma-separated post IDs"),
    window_hours: int = Query(default=24, ge=1, le=720),
) -> ActiveThreadsResponse:
    """
    Return activity data (velocity, recent comments, impression estimate)
    for a specific set of post IDs — the same posts shown on the results page.
    """
    _require_pool()
    post_ids = [i.strip() for i in ids.split(",") if i.strip()]
    if not post_ids:
        raise HTTPException(status_code=422, detail="No valid IDs provided")
    return await posts_repo.get_threads_activity(post_ids=post_ids, window_hours=window_hours)


@router.get("/{thread_id}", response_model=ThreadDetail)
async def get_thread(thread_id: str) -> ThreadDetail:
    """Returns a single post with all its comments."""
    _require_pool()
    result = await posts_repo.get_thread(thread_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Thread not found")
    return result
