"""
Alerts router — create user search alerts.
"""

from fastapi import APIRouter, HTTPException

import database
from models import AlertCreateRequest, AlertCreateResponse
from repositories import alerts as alerts_repo

router = APIRouter()


def _require_pool():
    if database._pool is None:
        raise HTTPException(
            status_code=503,
            detail="Database not available. Check DATABASE_URL configuration.",
        )


@router.post("", response_model=AlertCreateResponse)
async def create_alert(request: AlertCreateRequest) -> AlertCreateResponse:
    """
    Create an alert for a search query.
    Embeds the query via OpenAI and stores it with the user's email.
    """
    _require_pool()
    try:
        return await alerts_repo.create_alert(
            user_email=str(request.user_email),
            query=request.query,
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
