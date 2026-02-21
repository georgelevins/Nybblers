"""
Placeholder interfaces for drop-in integration later.
Agent code depends on these; implementations (Postgres, pgvector, Reddit, etc.) come later.
"""

from .schemas import AgentRequest, AgentResponse, RetrievalMatch


class Retriever:
    """Vector/search retriever. Stub now; implement with pgvector, Qdrant, etc."""

    def get_matches(self, query: str, limit: int = 20) -> list[RetrievalMatch]:
        return []


class Store:
    """Persist agent runs. Stub now; implement with Postgres etc."""

    async def save_run(self, request: AgentRequest, response: AgentResponse) -> None:
        pass


class RedditSource:
    """Reddit ingestion. Stub now; implement when Reddit pipeline exists."""

    def get_recent_threads(self, query: str, limit: int = 10) -> list[RetrievalMatch]:
        return []
