from models import Comment, OpportunityPost, SearchResultItem, ThreadDetail
from database import get_connection


def _vec_to_str(vec: list[float]) -> str:
    """Format a float list as a pgvector literal string."""
    return "[" + ",".join(str(x) for x in vec) + "]"


async def search_posts(
    query_embedding: list[float],
    subreddit: str | None,
    limit: int,
) -> list[SearchResultItem]:
    """Cosine similarity search over embedded post threads."""
    vec = _vec_to_str(query_embedding)
    async with get_connection() as conn:
        rows = await conn.fetch(
            """
            SELECT
                id,
                subreddit,
                title,
                created_utc,
                COALESCE(num_comments, 0)   AS num_comments,
                COALESCE(activity_ratio, 0) AS activity_ratio,
                last_comment_utc,
                1 - (embedding <=> $1::vector) AS similarity_score,
                LEFT(reconstructed_text, 300)   AS snippet
            FROM posts
            WHERE embedding IS NOT NULL
              AND ($2::text IS NULL OR subreddit = $2)
            ORDER BY embedding <=> $1::vector
            LIMIT $3
            """,
            vec,
            subreddit,
            limit,
        )

    return [
        SearchResultItem(
            id=r["id"],
            title=r["title"],
            subreddit=r["subreddit"],
            created_utc=r["created_utc"],
            num_comments=r["num_comments"],
            activity_ratio=r["activity_ratio"],
            last_comment_utc=r["last_comment_utc"],
            similarity_score=r["similarity_score"],
            snippet=r["snippet"] or "",
        )
        for r in rows
    ]


async def get_opportunities(
    subreddit: str | None,
    limit: int,
    min_activity_ratio: float,
) -> list[OpportunityPost]:
    """Return posts ordered by activity_ratio (highest = most evergreen)."""
    async with get_connection() as conn:
        rows = await conn.fetch(
            """
            SELECT
                id,
                subreddit,
                title,
                url,
                created_utc,
                COALESCE(num_comments, 0)   AS num_comments,
                COALESCE(activity_ratio, 0) AS activity_ratio,
                last_comment_utc
            FROM posts
            WHERE COALESCE(activity_ratio, 0) >= $3
              AND ($1::text IS NULL OR subreddit = $1)
            ORDER BY activity_ratio DESC NULLS LAST
            LIMIT $2
            """,
            subreddit,
            limit,
            min_activity_ratio,
        )

    return [
        OpportunityPost(
            id=r["id"],
            title=r["title"],
            subreddit=r["subreddit"],
            created_utc=r["created_utc"],
            num_comments=r["num_comments"],
            activity_ratio=r["activity_ratio"],
            last_comment_utc=r["last_comment_utc"],
            url=r["url"],
            ranks_on_google=False,  # not tracked yet
        )
        for r in rows
    ]


async def get_thread(thread_id: str) -> ThreadDetail | None:
    """Return a single post with all its comments, or None if not found."""
    async with get_connection() as conn:
        post = await conn.fetchrow(
            """
            SELECT id, subreddit, title, body, author, created_utc, score,
                   url, num_comments, last_comment_utc, recent_comment_count,
                   activity_ratio, reconstructed_text
            FROM posts
            WHERE id = $1
            """,
            thread_id,
        )
        if post is None:
            return None

        comment_rows = await conn.fetch(
            """
            SELECT id, post_id, parent_id, parent_type, author, body,
                   created_utc, COALESCE(score, 0) AS score,
                   COALESCE(controversiality, 0) AS controversiality
            FROM comments
            WHERE post_id = $1
            ORDER BY score DESC NULLS LAST
            """,
            thread_id,
        )

    comments = [
        Comment(
            id=c["id"],
            post_id=c["post_id"],
            parent_id=c["parent_id"],
            parent_type=c["parent_type"],
            author=c["author"],
            body=c["body"],
            created_utc=c["created_utc"],
            score=c["score"],
            controversiality=c["controversiality"],
        )
        for c in comment_rows
    ]

    return ThreadDetail(
        id=post["id"],
        subreddit=post["subreddit"],
        title=post["title"],
        body=post["body"],
        author=post["author"],
        created_utc=post["created_utc"],
        score=post["score"],
        url=post["url"],
        num_comments=post["num_comments"],
        last_comment_utc=post["last_comment_utc"],
        recent_comment_count=post["recent_comment_count"],
        activity_ratio=post["activity_ratio"],
        reconstructed_text=post["reconstructed_text"],
        comments=comments,
    )
