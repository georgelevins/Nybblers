# MOCK DATA — replace with real DB queries when schema is populated

from fastapi import APIRouter, HTTPException

from models import OpportunitiesResponse, ThreadDetail
from mock_data import MOCK_THREAD_ID, OPPORTUNITY_POSTS, THREAD_DETAIL

router = APIRouter()


@router.get("/opportunities", response_model=OpportunitiesResponse)
async def get_opportunities(
    subreddit: str | None = None,
    limit: int = 20,
    min_activity_ratio: float = 0.5,
) -> OpportunitiesResponse:
    """
    Returns posts sorted by activity_ratio descending.
    High activity ratio = evergreen thread likely indexed on Google.
    """
    results = [
        p for p in OPPORTUNITY_POSTS
        if p.activity_ratio >= min_activity_ratio
    ]
    if subreddit:
        results = [p for p in results if p.subreddit.lower() == subreddit.lower()]
    results = results[:limit]
    return OpportunitiesResponse(results=results)


@router.get("/{thread_id}", response_model=ThreadDetail)
async def get_thread(thread_id: str) -> ThreadDetail:
    """Returns a single post with all its comments as a nested array."""
    if thread_id != MOCK_THREAD_ID:
        raise HTTPException(status_code=404, detail="Thread not found")
    return THREAD_DETAIL
