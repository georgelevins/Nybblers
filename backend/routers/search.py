# MOCK DATA — replace with real DB queries when schema is populated

from fastapi import APIRouter

from models import SearchRequest, SearchResponse
from mock_data import SEARCH_RESULTS

router = APIRouter()


@router.post("", response_model=SearchResponse)
async def search(request: SearchRequest) -> SearchResponse:
    """
    Semantic search for Reddit threads matching the query.
    Returns threads from r/freelance and r/entrepreneur.
    """
    # TODO: embed query via OpenAI text-embedding-3-small, run pgvector cosine
    # similarity search, return real results. Swap mock_data for repository call.
    results = SEARCH_RESULTS
    if request.subreddit:
        results = [r for r in results if r.subreddit.lower() == request.subreddit.lower()]
    return SearchResponse(results=results[: request.limit])
