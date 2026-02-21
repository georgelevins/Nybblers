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


async def init_pool() -> None:
    """Initialize the connection pool. Call on app startup."""
    global _pool
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        # Allow app to run without DB for mock-only mode
        return
    _pool = await asyncpg.create_pool(
        database_url,
        min_size=1,
        max_size=10,
        command_timeout=60,
    )


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
