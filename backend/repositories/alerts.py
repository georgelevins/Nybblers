"""
Alerts repository — create and list user alerts with query embeddings.
"""

from models import AlertCreateResponse
from database import get_pool
from repositories.embeddings import embed_text, to_pg_vector


async def create_alert(user_email: str, query: str) -> AlertCreateResponse:
    """Embed the query and INSERT a new alert row. Returns the created alert."""
    embedding = await embed_text(query)
    vec = to_pg_vector(embedding)
    pool = await get_pool()

    sql = """
        INSERT INTO alerts (user_email, query, query_embedding)
        VALUES ($1, $2, $3::vector)
        RETURNING id, user_email, query, created_at
    """

    async with pool.acquire() as conn:
        row = await conn.fetchrow(sql, user_email, query, vec)

    return AlertCreateResponse(
        id=row["id"],
        user_email=row["user_email"],
        query=row["query"],
        created_at=row["created_at"],
    )
