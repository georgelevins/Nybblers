from models import (
    Comment,
    DemandCountResponse,
    LeadResultItem,
    OpportunityPost,
    SearchResultItem,
    ThreadDetail,
)
from database import get_connection


def _reddit_post_url(post_id: str, subreddit: str) -> str:
    sub = (subreddit or "reddit").strip().lstrip("/")
    return f"https://reddit.com/r/{sub}/comments/{post_id}"


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
                author,
                created_utc,
                COALESCE(num_comments, 0)       AS num_comments,
                COALESCE(recent_comment_count, 0) AS recent_comment_count,
                COALESCE(activity_ratio, 0)     AS activity_ratio,
                last_comment_utc,
                1 - (embedding <=> $1::vector)  AS similarity_score,
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
            author=r["author"],
            created_utc=r["created_utc"],
            num_comments=r["num_comments"],
            recent_comment_count=r["recent_comment_count"],
            activity_ratio=r["activity_ratio"],
            last_comment_utc=r["last_comment_utc"],
            similarity_score=r["similarity_score"],
            snippet=r["snippet"] or "",
        )
        for r in rows
    ]


async def get_demand_count(
    query_embedding: list[float],
    subreddit: str | None,
    min_similarity: float,
) -> DemandCountResponse:
    """Count posts (and distinct authors) above similarity threshold."""
    vec = _vec_to_str(query_embedding)
    async with get_connection() as conn:
        row = await conn.fetchrow(
            """
            SELECT
                COUNT(*) AS matching_posts,
                COUNT(DISTINCT author) FILTER (WHERE author IS NOT NULL AND author != '') AS distinct_authors,
                COALESCE(SUM(num_comments), 0)::bigint AS total_comments_on_matching
            FROM posts
            WHERE embedding IS NOT NULL
              AND ($2::text IS NULL OR subreddit = $2)
              AND (1 - (embedding <=> $1::vector)) >= $3
            """,
            vec,
            subreddit,
            min_similarity,
        )
    return DemandCountResponse(
        matching_posts=row["matching_posts"],
        distinct_authors=row["distinct_authors"],
        total_comments_on_matching=row["total_comments_on_matching"],
    )


async def search_leads(
    query_embedding: list[float],
    subreddit: str | None,
    limit: int,
    min_similarity: float,
) -> list[LeadResultItem]:
    """Search comment_embeddings for leads; return comment + author + post link."""
    vec = _vec_to_str(query_embedding)
    async with get_connection() as conn:
        rows = await conn.fetch(
            """
            SELECT
                c.id AS comment_id,
                c.post_id,
                c.author,
                LEFT(c.body, 400) AS snippet,
                1 - (e.embedding <=> $1::vector) AS similarity_score,
                p.subreddit
            FROM comment_embeddings e
            JOIN comments c ON c.id = e.comment_id
            JOIN posts p ON p.id = c.post_id
            WHERE ($2::text IS NULL OR p.subreddit = $2)
              AND (1 - (e.embedding <=> $1::vector)) >= $4
            ORDER BY e.embedding <=> $1::vector
            LIMIT $3
            """,
            vec,
            subreddit,
            limit,
            min_similarity,
        )
    return [
        LeadResultItem(
            comment_id=r["comment_id"],
            post_id=r["post_id"],
            author=r["author"],
            snippet=(r["snippet"] or "").strip(),
            similarity_score=r["similarity_score"],
            post_url=_reddit_post_url(r["post_id"], r["subreddit"]),
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
