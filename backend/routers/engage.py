"""
Engage router: endpoints for the engagement campaign feature.
"""

from fastapi import APIRouter
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
    Generate an AI-drafted Reddit reply for the given thread.
    Uses Claude to write a genuine, non-promotional reply that adds value.
    """
    system = (
        "You are writing a genuine, helpful Reddit reply. "
        "The reply must be driven by what the user has provided as their business idea or topic — that is the main basis for your response. "
        "Connect it naturally to the thread so your reply fits the conversation; do not ignore the thread. "
        "Be concise (2-4 sentences), conversational, and non-promotional (add value, don't pitch). "
        "Return only the reply text — no preamble, no quotes around it."
    )
    user = (
        f"What the user entered (this is the basis for your reply): {req.query}\n\n"
        f'Thread they are replying to: r/{req.thread_subreddit} — "{req.thread_title}"\n\n'
        "Write a reply that is based on the user's input above and that fits naturally as a helpful response in this thread."
    )
    draft = complete(system=system, user=user, max_tokens=300)
    return DraftReplyResponse(draft=draft)
