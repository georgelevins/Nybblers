#!/usr/bin/env python3
"""
Generate or update .mcp.json so the Postgres MCP server gets DB credentials from backend/.env.

The Postgres MCP often expects DB_PASSWORD (and sometimes DATABASE_URL, DB_HOST, etc.).
Cursor does not expand $VAR in mcp.json, so this script reads backend/.env, parses
DATABASE_URL, and writes the env block into .mcp.json.

Usage:
  python scripts/setup_mcp_postgres.py

  From repo root; creates or updates .mcp.json in the repo root.
  If .mcp.json already exists, it adds/updates the "env" of the first server whose
  name contains "Postgres" or "RedditDemand". Otherwise it creates a minimal
  Postgres MCP entry (you may need to adjust "command" and "args" for your MCP).
"""

import json
import os
import re
import sys
from pathlib import Path
from urllib.parse import urlparse, unquote

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

REPO_ROOT = Path(__file__).resolve().parent.parent
BACKEND_ENV = REPO_ROOT / "backend" / ".env"
MCP_JSON = REPO_ROOT / ".mcp.json"


def parse_database_url(url: str) -> dict[str, str]:
    """Parse postgresql://user:pass@host:port/db into components."""
    if not url or not url.strip():
        return {}
    url = url.strip()
    if not url.startswith(("postgresql://", "postgres://")):
        url = "postgresql://" + url.lstrip("://")
    try:
        p = urlparse(url)
        return {
            "DATABASE_URL": url if "://" in url else f"postgresql://{url}",
            "DB_HOST": p.hostname or "",
            "DB_PORT": str(p.port or 5432),
            "DB_USER": unquote(p.username) if p.username else "",
            "DB_PASSWORD": unquote(p.password) if p.password else "",
            "DB_NAME": (p.path or "").lstrip("/").split("?")[0] or "",
        }
    except Exception:
        return {}


def main() -> None:
    if load_dotenv is None:
        print("Install python-dotenv: pip install python-dotenv", file=sys.stderr)
        sys.exit(1)

    if not BACKEND_ENV.exists():
        print(f"Missing {BACKEND_ENV}. Create it from backend/.env.example and set DATABASE_URL.", file=sys.stderr)
        sys.exit(1)

    load_dotenv(BACKEND_ENV)
    url = os.getenv("DATABASE_URL")
    env = parse_database_url(url or "")
    if not env.get("DB_PASSWORD") and not env.get("DATABASE_URL"):
        print("DATABASE_URL in backend/.env is missing or has no password.", file=sys.stderr)
        sys.exit(1)

    # Load or create .mcp.json
    if MCP_JSON.exists():
        try:
            data = json.loads(MCP_JSON.read_text())
        except Exception as e:
            print(f"Could not read {MCP_JSON}: {e}", file=sys.stderr)
            sys.exit(1)
        servers = data.get("mcpServers") or {}
    else:
        data = {"mcpServers": {}}
        servers = data["mcpServers"]

    # Find a Postgres-related server to update, or create one
    postgres_key = None
    for key in servers:
        if "postgres" in key.lower() or "reddit" in key.lower():
            postgres_key = key
            break

    if postgres_key:
        if "env" not in servers[postgres_key]:
            servers[postgres_key]["env"] = {}
        servers[postgres_key]["env"].update(env)
        print(f"Updated env for server '{postgres_key}' in {MCP_JSON}")
    else:
        # Create entry for official Postgres MCP (connection URL in args) and also set env
        # so MCPs that expect DB_PASSWORD / DATABASE_URL get them
        postgres_key = "Postgres_RedditDemand"
        conn_url = env.get("DATABASE_URL", "postgresql://localhost/postgres")
        servers[postgres_key] = {
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-postgres", conn_url],
            "env": env,
        }
        print(f"Added server '{postgres_key}' to {MCP_JSON} with connection from backend/.env")
        data["mcpServers"] = servers

    MCP_JSON.write_text(json.dumps(data, indent=2))
    print("Done. Restart Cursor or reload MCP so the Postgres server picks up the env.")


if __name__ == "__main__":
    main()
