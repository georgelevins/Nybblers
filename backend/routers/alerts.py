from fastapi import APIRouter, HTTPException

from models import AlertCreateRequest, AlertCreateResponse
from openai_utils import embed_text
import repositories.alerts as alerts_repo

router = APIRouter()


@router.post("", response_model=AlertCreateResponse)
async def create_alert(request: AlertCreateRequest) -> AlertCreateResponse:
    """
    Create an alert for a search query.
    The query is embedded so future posts can be matched against it.
    """
    try:
        query_embedding = await embed_text(request.query)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Embedding failed: {exc}") from exc

    return await alerts_repo.create_alert(
        user_email=str(request.user_email),
        query=request.query,
        query_embedding=query_embedding,
    )
