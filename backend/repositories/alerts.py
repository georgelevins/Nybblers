from models import AlertCreateResponse
from database import get_connection


def _vec_to_str(vec: list[float]) -> str:
    return "[" + ",".join(str(x) for x in vec) + "]"


async def create_alert(
    user_email: str,
    query: str,
    query_embedding: list[float],
) -> AlertCreateResponse:
    """Insert a new alert row and return the created record."""
    vec = _vec_to_str(query_embedding)
    async with get_connection() as conn:
        row = await conn.fetchrow(
            """
            INSERT INTO alerts (user_email, query, query_embedding)
            VALUES ($1, $2, $3::vector)
            RETURNING id, user_email, query, created_at
            """,
            user_email,
            query,
            vec,
        )

    return AlertCreateResponse(
        id=row["id"],
        user_email=row["user_email"],
        query=row["query"],
        created_at=row["created_at"],
    )
