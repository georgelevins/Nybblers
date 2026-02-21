# TODO: implement when schema is final
# Use database.get_pool() for connections.
# Swap mock_data calls in routers for these functions.

# async def search_posts(
#     query_embedding: list[float],
#     subreddit: str | None,
#     limit: int,
# ) -> list[SearchResultItem]:
#     """Embed query via OpenAI, run pgvector cosine similarity, return results."""
#     ...
#
# async def get_opportunities(
#     subreddit: str | None,
#     limit: int,
#     min_activity_ratio: float,
# ) -> list[OpportunityPost]:
#     """SELECT * FROM posts ORDER BY activity_ratio DESC ..."""
#     ...
#
# async def get_thread(thread_id: str) -> ThreadDetail | None:
#     """SELECT post + comments, build ThreadDetail."""
#     ...
