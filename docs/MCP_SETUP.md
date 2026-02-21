# Postgres MCP setup

The Postgres MCP lets Cursor query your RedditDemand database (schema, run read-only queries). The MCP server needs your database credentials.

## Quick fix (recommended)

From the repo root, run:

```bash
python scripts/setup_mcp_postgres.py
```

This reads `backend/.env`, parses `DATABASE_URL`, and:

- **If `.mcp.json` already exists** — adds or updates the `env` block for the first server whose name contains "Postgres" or "RedditDemand" with `DB_PASSWORD`, `DATABASE_URL`, `DB_HOST`, etc.
- **If `.mcp.json` does not exist** — creates it with a Postgres MCP server entry using the connection URL from your `.env`.

Then **restart Cursor** (or reload MCP) so the server picks up the new config.

## Manual setup

1. Copy the example and fill in credentials (do not commit the real file):

   ```bash
   cp .mcp.json.example .mcp.json
   # Edit .mcp.json and replace USER, PASSWORD, HOST, DATABASE with your values.
   ```

2. Or in Cursor: **Settings → MCP → your Postgres server → Environment variables**, and add at least:
   - `DB_PASSWORD` — your database password (from `DATABASE_URL` in `backend/.env`: the part after the colon after the username, before `@`).

   If your MCP expects a full URL, also set:
   - `DATABASE_URL` — same value as in `backend/.env`.

3. `.mcp.json` is gitignored so credentials stay local.

## Verify

After restarting Cursor, you can ask the AI to “list tables in public” or “describe the posts table” — it will use the Postgres MCP. If you see `DB_PASSWORD environment variable is required`, the server is not receiving the env; run `python scripts/setup_mcp_postgres.py` again and restart Cursor.
