from fastapi import APIRouter, HTTPException

from models import OpportunitiesResponse, ThreadDetail
import repositories.posts as posts_repo

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
    results = await posts_repo.get_opportunities(
        subreddit=subreddit,
        limit=limit,
        min_activity_ratio=min_activity_ratio,
    )
    return OpportunitiesResponse(results=results)


@router.get("/{thread_id}", response_model=ThreadDetail)
async def get_thread(thread_id: str) -> ThreadDetail:
    """Returns a single post with all its comments as a nested array."""
    thread = await posts_repo.get_thread(thread_id)
    if thread is None:
        raise HTTPException(status_code=404, detail="Thread not found")
    return thread
