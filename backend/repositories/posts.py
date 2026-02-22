"""
Post repository — real asyncpg + pgvector queries.
All functions embed the query text via OpenAI before searching.
"""

from datetime import datetime

from database import get_pool
from models import (
    ActiveThread,
    ActiveThreadsResponse,
    Comment,
    GrowthMomentumResponse,
    MentionsTrendResponse,
    SearchResponse,
    SearchResultItem,
    SubredditUsersResponse,
    ThreadDetail,
    TimePoint,
    TopMatch,
    TopMatchesResponse,
)
from repositories.embeddings import embed_text, to_pg_vector

# Cosine distance threshold — lower = more similar (0 = identical, 2 = opposite)
SIMILARITY_THRESHOLD = 0.7


async def search_posts(
    query_text: str,
    subreddit: str | None = None,
    limit: int = 20,
) -> SearchResponse:
    """Embed query, run pgvector cosine similarity search on posts, return SearchResponse."""
    embedding = await embed_text(query_text)
    pool = await get_pool()

    base_sql = """
        SELECT
            id, title, subreddit, created_utc, num_comments,
            COALESCE(activity_ratio, 0.0) AS activity_ratio,
            last_comment_utc,
            1 - (embedding <=> $1::vector) AS similarity_score,
            COALESCE(reconstructed_text, body, title) AS snippet
        FROM posts
        WHERE embedding IS NOT NULL
          AND embedding <=> $1::vector < $2
        {subreddit_filter}
        ORDER BY embedding <=> $1::vector
        LIMIT $3
    """
    vec = to_pg_vector(embedding)
    params: list = [vec, SIMILARITY_THRESHOLD, limit]
    subreddit_filter = ""
    if subreddit:
        subreddit_filter = "AND subreddit = $4"
        params.append(subreddit)

    sql = base_sql.format(subreddit_filter=subreddit_filter)

    async with pool.acquire() as conn:
        rows = await conn.fetch(sql, *params)

    results = [
        SearchResultItem(
            id=row["id"],
            title=row["title"],
            subreddit=row["subreddit"],
            created_utc=row["created_utc"],
            num_comments=row["num_comments"] or 0,
            activity_ratio=row["activity_ratio"] or 0.0,
            last_comment_utc=row["last_comment_utc"],
            similarity_score=float(row["similarity_score"]),
            snippet=(row["snippet"] or "")[:300],
        )
        for row in rows
    ]
    return SearchResponse(results=results)


async def get_top_matches(
    query_text: str,
    limit: int = 10,
) -> TopMatchesResponse:
    """
    Return the most semantically similar posts and comments combined.
    Posts come from `posts` table; comments from `comments` JOIN `comment_embeddings`.
    """
    embedding = await embed_text(query_text)
    vec = to_pg_vector(embedding)
    pool = await get_pool()

    # Top matching posts
    post_sql = """
        SELECT
            p.id,
            p.subreddit,
            p.author,
            COALESCE(p.body, p.title) AS body,
            COALESCE(p.score, 0) AS score,
            p.url,
            1 - (p.embedding <=> $1::vector) AS similarity,
            'post' AS kind
        FROM posts p
        WHERE p.embedding IS NOT NULL
          AND p.embedding <=> $1::vector < $2
        ORDER BY p.embedding <=> $1::vector
        LIMIT $3
    """

    # Top matching comments (via comment_embeddings)
    comment_sql = """
        SELECT
            c.id,
            p.subreddit,
            c.author,
            c.body,
            COALESCE(c.score, 0) AS score,
            NULL AS url,
            1 - (ce.embedding <=> $1::vector) AS similarity,
            'comment' AS kind
        FROM comments c
        JOIN comment_embeddings ce ON ce.comment_id = c.id
        LEFT JOIN posts p ON p.id = c.post_id
        WHERE ce.embedding <=> $1::vector < $2
        ORDER BY ce.embedding <=> $1::vector
        LIMIT $3
    """

    async with pool.acquire() as conn:
        post_rows = await conn.fetch(post_sql, vec, SIMILARITY_THRESHOLD, limit)
        comment_rows = await conn.fetch(comment_sql, vec, SIMILARITY_THRESHOLD, limit)

    combined: list[TopMatch] = []
    for row in post_rows:
        combined.append(
            TopMatch(
                id=row["id"],
                subreddit=row["subreddit"],
                author=row["author"],
                body=(row["body"] or "")[:500],
                score=row["score"],
                url=row["url"],
                similarity=float(row["similarity"]),
                kind="post",
            )
        )
    for row in comment_rows:
        combined.append(
            TopMatch(
                id=row["id"],
                subreddit=row["subreddit"],
                author=row["author"],
                body=(row["body"] or "")[:500],
                score=row["score"],
                url=None,
                similarity=float(row["similarity"]),
                kind="comment",
            )
        )

    # Sort combined by similarity descending, return top `limit`
    combined.sort(key=lambda m: m.similarity, reverse=True)
    return TopMatchesResponse(matches=combined[:limit])


async def get_mentions_over_time(query_text: str) -> MentionsTrendResponse:
    """
    Monthly count of posts semantically similar to the query.
    Returns a time series sorted oldest-first.
    """
    embedding = await embed_text(query_text)
    vec = to_pg_vector(embedding)
    pool = await get_pool()

    sql = """
        SELECT
            TO_CHAR(created_utc, 'YYYY-MM') AS month,
            COUNT(*) AS cnt
        FROM posts
        WHERE embedding IS NOT NULL
          AND embedding <=> $1::vector < $2
        GROUP BY month
        ORDER BY month
    """

    async with pool.acquire() as conn:
        rows = await conn.fetch(sql, vec, SIMILARITY_THRESHOLD)

    points = [
        TimePoint(
            date=f"{row['month']}-01",
            label=_format_month_label(row["month"]),
            value=int(row["cnt"]),
        )
        for row in rows
    ]
    return MentionsTrendResponse(points=points)


async def get_users_by_subreddit(
    query_text: str,
    limit: int = 50,
) -> SubredditUsersResponse:
    """
    Unique authors per subreddit from posts similar to the query.
    Returns { subreddit: [username, ...] }.
    """
    embedding = await embed_text(query_text)
    vec = to_pg_vector(embedding)
    pool = await get_pool()

    sql = """
        SELECT subreddit, author
        FROM posts
        WHERE embedding IS NOT NULL
          AND embedding <=> $1::vector < $2
          AND author IS NOT NULL
          AND author <> '[deleted]'
          AND author <> 'AutoModerator'
        ORDER BY embedding <=> $1::vector
        LIMIT $3
    """

    async with pool.acquire() as conn:
        rows = await conn.fetch(sql, vec, SIMILARITY_THRESHOLD, limit)

    subreddits: dict[str, list[str]] = {}
    seen: set[tuple[str, str]] = set()
    for row in rows:
        sub = f"r/{row['subreddit']}"
        author = row["author"]
        if (sub, author) not in seen:
            seen.add((sub, author))
            subreddits.setdefault(sub, []).append(author)

    return SubredditUsersResponse(subreddits=subreddits)


async def get_growth_data(query_text: str) -> GrowthMomentumResponse:
    """
    Weekly and monthly time series of post counts similar to the query.
    """
    embedding = await embed_text(query_text)
    vec = to_pg_vector(embedding)
    pool = await get_pool()

    monthly_sql = """
        SELECT
            TO_CHAR(created_utc, 'YYYY-MM') AS period,
            COUNT(*) AS cnt
        FROM posts
        WHERE embedding IS NOT NULL
          AND embedding <=> $1::vector < $2
        GROUP BY period
        ORDER BY period
    """

    weekly_sql = """
        SELECT
            TO_CHAR(DATE_TRUNC('week', created_utc), 'YYYY-MM-DD') AS period,
            COUNT(*) AS cnt
        FROM posts
        WHERE embedding IS NOT NULL
          AND embedding <=> $1::vector < $2
        GROUP BY period
        ORDER BY period
    """

    async with pool.acquire() as conn:
        monthly_rows = await conn.fetch(monthly_sql, vec, SIMILARITY_THRESHOLD)
        weekly_rows = await conn.fetch(weekly_sql, vec, SIMILARITY_THRESHOLD)

    monthly = [
        TimePoint(
            date=f"{row['period']}-01",
            label=_format_month_label(row["period"]),
            value=int(row["cnt"]),
        )
        for row in monthly_rows
    ]

    weekly = [
        TimePoint(
            date=row["period"],
            label=_format_week_label(row["period"]),
            value=int(row["cnt"]),
        )
        for row in weekly_rows
    ]

    return GrowthMomentumResponse(weekly=weekly, monthly=monthly)


async def get_thread(thread_id: str) -> ThreadDetail | None:
    """Fetch a single post with all its comments."""
    pool = await get_pool()

    async with pool.acquire() as conn:
        post_row = await conn.fetchrow(
            "SELECT * FROM posts WHERE id = $1",
            thread_id,
        )
        if post_row is None:
            return None

        comment_rows = await conn.fetch(
            """
            SELECT id, post_id, parent_id, parent_type, author, body,
                   created_utc, COALESCE(score, 0) AS score,
                   COALESCE(controversiality, 0) AS controversiality
            FROM comments
            WHERE post_id = $1
            ORDER BY created_utc
            """,
            thread_id,
        )

    comments = [
        Comment(
            id=r["id"],
            post_id=r["post_id"],
            parent_id=r["parent_id"],
            parent_type=r["parent_type"],
            author=r["author"],
            body=r["body"],
            created_utc=r["created_utc"],
            score=r["score"],
            controversiality=r["controversiality"],
        )
        for r in comment_rows
    ]

    return ThreadDetail(
        id=post_row["id"],
        subreddit=post_row["subreddit"],
        title=post_row["title"],
        body=post_row["body"],
        author=post_row["author"],
        created_utc=post_row["created_utc"],
        score=post_row["score"],
        url=post_row["url"],
        num_comments=post_row["num_comments"],
        last_comment_utc=post_row["last_comment_utc"],
        recent_comment_count=post_row["recent_comment_count"],
        activity_ratio=post_row["activity_ratio"],
        reconstructed_text=post_row["reconstructed_text"],
        comments=comments,
    )


async def get_threads_activity(
    post_ids: list[str],
    window_hours: int = 24,
) -> ActiveThreadsResponse:
    """
    Return activity data for a specific set of post IDs.
    Used by the engage page to show the same threads as the results page,
    enriched with recent comment velocity.
    """
    if not post_ids:
        return ActiveThreadsResponse(active_count=0, total_estimated_impressions=0, window_hours=window_hours, threads=[])

    pool = await get_pool()

    sql = """
        WITH active AS (
            SELECT
                p.id,
                p.title,
                p.subreddit,
                p.url,
                p.last_comment_utc,
                COALESCE(p.score, 0)        AS score,
                COALESCE(p.num_comments, 0) AS num_comments,
                COUNT(c.id) FILTER (
                    WHERE c.created_utc >= p.last_comment_utc - ($2 * INTERVAL '1 hour')
                ) AS recent_comments
            FROM posts p
            LEFT JOIN comments c ON c.post_id = p.id
            WHERE p.id = ANY($1)
              AND p.last_comment_utc IS NOT NULL
            GROUP BY p.id, p.title, p.subreddit, p.url,
                     p.last_comment_utc, p.score, p.num_comments
        )
        SELECT *, recent_comments::float / GREATEST(1, $2) AS velocity
        FROM active
        ORDER BY velocity DESC
    """

    async with pool.acquire() as conn:
        rows = await conn.fetch(sql, post_ids, float(window_hours))

    threads = [
        ActiveThread(
            id=r["id"],
            title=r["title"],
            subreddit=r["subreddit"],
            url=r["url"],
            last_comment_utc=r["last_comment_utc"],
            score=r["score"],
            num_comments=r["num_comments"],
            recent_comments=int(r["recent_comments"]),
            velocity=float(r["velocity"]),
            estimated_impressions=r["score"] * 4 + r["num_comments"] * 100,
        )
        for r in rows
    ]

    total_impressions = sum(t.estimated_impressions for t in threads)
    return ActiveThreadsResponse(
        active_count=len(threads),
        total_estimated_impressions=total_impressions,
        window_hours=window_hours,
        threads=threads,
    )


async def get_active_threads(
    query_text: str,
    window_hours: int = 24,
    min_comments: int = 3,
    limit: int = 20,
) -> ActiveThreadsResponse:
    """
    Return semantically relevant posts that had recent comment activity.

    'Active' is defined as: ≥ min_comments comments posted within the
    window_hours period immediately before the thread's last_comment_utc.
    This is relative to the thread's own activity peak (not today's date),
    so it works correctly with Pushshift dump data.

    Velocity = recent_comments / window_hours — higher means faster discussion.
    """
    embedding = await embed_text(query_text)
    vec = to_pg_vector(embedding)
    pool = await get_pool()

    sql = """
        WITH active AS (
            SELECT
                p.id,
                p.title,
                p.subreddit,
                p.url,
                p.last_comment_utc,
                COALESCE(p.score, 0)        AS score,
                COALESCE(p.num_comments, 0) AS num_comments,
                COUNT(c.id) FILTER (
                    WHERE c.created_utc >= p.last_comment_utc - ($3 * INTERVAL '1 hour')
                ) AS recent_comments
            FROM posts p
            JOIN comments c ON c.post_id = p.id
            WHERE p.embedding IS NOT NULL
              AND p.embedding <=> $1::vector < $2
              AND p.last_comment_utc IS NOT NULL
            GROUP BY p.id, p.title, p.subreddit, p.url,
                     p.last_comment_utc, p.score, p.num_comments
            HAVING COUNT(c.id) FILTER (
                WHERE c.created_utc >= p.last_comment_utc - ($3 * INTERVAL '1 hour')
            ) >= $4
        )
        SELECT
            *,
            recent_comments::float / GREATEST(1, $3) AS velocity
        FROM active
        ORDER BY velocity DESC
        LIMIT $5
    """

    async with pool.acquire() as conn:
        rows = await conn.fetch(sql, vec, SIMILARITY_THRESHOLD, float(window_hours), min_comments, limit)

    threads = [
        ActiveThread(
            id=r["id"],
            title=r["title"],
            subreddit=r["subreddit"],
            url=r["url"],
            last_comment_utc=r["last_comment_utc"],
            score=r["score"],
            num_comments=r["num_comments"],
            recent_comments=int(r["recent_comments"]),
            velocity=float(r["velocity"]),
            estimated_impressions=r["score"] * 4 + r["num_comments"] * 100,
        )
        for r in rows
    ]

    total_impressions = sum(t.estimated_impressions for t in threads)
    return ActiveThreadsResponse(
        active_count=len(threads),
        total_estimated_impressions=total_impressions,
        window_hours=window_hours,
        threads=threads,
    )


# --- Helpers ---


def _format_month_label(ym: str) -> str:
    """Turn '2023-06' → 'Jun 23'."""
    try:
        dt = datetime.strptime(ym, "%Y-%m")
        return dt.strftime("%b %y")
    except ValueError:
        return ym


def _format_week_label(date_str: str) -> str:
    """Turn '2023-06-05' → 'Jun 05'."""
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        return dt.strftime("%b %d")
    except ValueError:
        return date_str
