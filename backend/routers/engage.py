"""
Engage router: endpoints for the engagement campaign feature.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from agent.claude_client import complete

router = APIRouter()


class DraftReplyRequest(BaseModel):
    thread_title: str
    thread_subreddit: str
    query: str  # user's search topic / product idea


class DraftReplyResponse(BaseModel):
    draft: str


@router.post("/draft-reply", response_model=DraftReplyResponse)
def draft_reply(req: DraftReplyRequest) -> DraftReplyResponse:
    """
    Generate an AI-drafted Reddit reply where the user recommends their own product.
    Uses Claude with a prompt that centers on the user's input (req.query = business idea/product)
    and writes a first-person reply that mentions/recommends that product in the thread.
    """
    system = (
        "You are writing a Reddit reply where the user is recommending their own product or business to someone in the thread. "
        "The reply must specifically mention and recommend the exact product/tool the user described — by name if they gave one (e.g. FreeVoice). "
        "Write as the user: first-person, genuine, helpful (e.g. 'I built...', 'I use X for...', 'Something like [their product] could help because...'). "
        "Do not recommend other tools or platforms; the reply is about the user's own product fitting the thread. "
        "Be concise (2-4 sentences), conversational, and natural — not salesy. "
        "Return only the reply text — no preamble, no quotes around it."
    )
    user = (
        f"The user's own product/business (they are recommending this in the reply): {req.query}\n\n"
        f'Thread they are replying to: r/{req.thread_subreddit} — "{req.thread_title}"\n\n'
        "Write a reply where the user recommends their product above in a natural, helpful way that fits this thread. Mention their product by name or clearly. Do not suggest other tools."
    )
    try:
        draft = complete(system=system, user=user, max_tokens=300)
        return DraftReplyResponse(draft=draft)
    except RuntimeError as e:
        if "API key" in str(e) or "ANTHROPIC_API_KEY" in str(e):
            raise HTTPException(
                status_code=503,
                detail="AI draft not configured (missing ANTHROPIC_API_KEY). Set it in backend .env.",
            )
        raise HTTPException(status_code=502, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Claude API error: {e!s}")
