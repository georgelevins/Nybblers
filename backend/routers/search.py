from fastapi import APIRouter, HTTPException

from models import SearchRequest, SearchResponse
from openai_utils import embed_text
import repositories.posts as posts_repo

router = APIRouter()


@router.post("", response_model=SearchResponse)
async def search(request: SearchRequest) -> SearchResponse:
    """
    Semantic search for Reddit threads matching the query.
    Embeds the query via OpenAI then runs pgvector cosine similarity.
    """
    try:
        query_embedding = await embed_text(request.query)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Embedding failed: {exc}") from exc

    results = await posts_repo.search_posts(
        query_embedding=query_embedding,
        subreddit=request.subreddit,
        limit=request.limit,
    )
    return SearchResponse(results=results)
