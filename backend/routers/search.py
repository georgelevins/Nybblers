from fastapi import APIRouter, HTTPException

from models import (
    DemandCountRequest,
    DemandCountResponse,
    SearchLeadsRequest,
    SearchLeadsResponse,
    SearchRequest,
    SearchResponse,
)
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


@router.post("/demand", response_model=DemandCountResponse)
async def demand_count(request: DemandCountRequest) -> DemandCountResponse:
    """
    Demand count: how many people (posts) and distinct authors match the problem.
    Embeds the query and counts posts above min_similarity threshold.
    """
    try:
        query_embedding = await embed_text(request.query)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Embedding failed: {exc}") from exc

    return await posts_repo.get_demand_count(
        query_embedding=query_embedding,
        subreddit=request.subreddit,
        min_similarity=request.min_similarity,
    )


@router.post("/leads", response_model=SearchLeadsResponse)
async def search_leads(request: SearchLeadsRequest) -> SearchLeadsResponse:
    """
    Leads: surface people having the problem (comment-level search).
    Searches comment_embeddings and returns matching comments with author and thread link.
    Requires comment embeddings to be populated (embed_comments.py).
    """
    try:
        query_embedding = await embed_text(request.query)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Embedding failed: {exc}") from exc

    results = await posts_repo.search_leads(
        query_embedding=query_embedding,
        subreddit=request.subreddit,
        limit=request.limit,
        min_similarity=request.min_similarity,
    )
    return SearchLeadsResponse(results=results)
