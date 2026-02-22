"""
Database connection pool for RedditDemand.
Manages asyncpg connections to Supabase Postgres.
No queries in this file — use repositories/ when schema is ready.
"""

import os
from contextlib import asynccontextmanager

import asyncpg


_pool: asyncpg.Pool | None = None


async def get_pool() -> asyncpg.Pool:
    """Get the connection pool. Raises if not initialized."""
    if _pool is None:
        raise RuntimeError("Database pool not initialized. Call init_pool() first.")
    return _pool


def _is_placeholder_db_url(url: str) -> bool:
    """True if URL looks like .env.example placeholder (not a real host)."""
    if not url or not url.strip():
        return True
    lower = url.lower()
    # Skip placeholder examples so app can start without a real DB
    if "user:pass" in lower or "@host:" in lower or "host:5432" in lower:
        return True
    return False


async def init_pool() -> None:
    """Initialize the connection pool. Call on app startup. Skips if no DB URL or placeholder."""
    global _pool
    database_url = (os.getenv("DATABASE_URL") or "").strip()
    if not database_url or _is_placeholder_db_url(database_url):
        return
    try:
        _pool = await asyncpg.create_pool(
            database_url,
            min_size=5,
            max_size=20,
            command_timeout=60,
        )
    except Exception:
        # DB unreachable (e.g. wrong host, no network) — leave pool None so app still starts
        _pool = None


async def close_pool() -> None:
    """Close the connection pool. Call on app shutdown."""
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None


@asynccontextmanager
async def get_connection():
    """
    Context manager for acquiring a connection from the pool.
    Use when implementing repository queries.
    """
    pool = await get_pool()
    async with pool.acquire() as conn:
        yield conn
