# MOCK DATA — replace with real DB queries when schema is populated

from datetime import datetime
from uuid import uuid4

from fastapi import APIRouter

from models import AlertCreateRequest, AlertCreateResponse

router = APIRouter()


@router.post("", response_model=AlertCreateResponse)
async def create_alert(request: AlertCreateRequest) -> AlertCreateResponse:
    """
    Create an alert for a search query.
    User will be notified when new matching posts appear.
    """
    # TODO: INSERT INTO alerts (user_email, query, query_embedding, ...)
    # Embed query via OpenAI first, then insert. Use database.get_pool() for connection.
    created_at = datetime.utcnow()
    alert_id = uuid4()
    return AlertCreateResponse(
        id=alert_id,
        user_email=request.user_email,
        query=request.query,
        created_at=created_at,
    )
