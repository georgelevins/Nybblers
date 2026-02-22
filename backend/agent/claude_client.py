"""
LLM wrapper for the agent. Uses Anthropic (Claude) API.
Enforces: JSON-only output (via prompt), token limit, low temperature.
"""

import json
import os
from pathlib import Path
from typing import Any

from anthropic import Anthropic


# Contract constants
# Use -latest alias; snapshot claude-3-5-sonnet-20241022 was deprecated (404)
DEFAULT_MODEL = "claude-3-5-sonnet-latest"
MAX_OUTPUT_TOKENS = 4096
TEMPERATURE = 0.2  # Low for consistent, deterministic outputs


def _load_prompt(name: str, version: str = "v1") -> str:
    """Load prompt from agent/prompts/<name>_<version>.txt."""
    base = Path(__file__).resolve().parent / "prompts"
    path = base / f"{name}_{version}.txt"
    if not path.exists():
        path = base / f"{name}.txt"
    return path.read_text(encoding="utf-8").strip()


def complete(
    system: str,
    user: str,
    *,
    model: str | None = None,
    max_tokens: int = MAX_OUTPUT_TOKENS,
    temperature: float = TEMPERATURE,
) -> str:
    """
    Call Anthropic (Claude) with system + user message. Returns raw text.
    Use parse_json_response() on the result for structured output.
    """
    # Ensure .env is loaded (backend/.env) in case it wasn't at startup
    from dotenv import load_dotenv
    _backend_dir = Path(__file__).resolve().parent.parent
    load_dotenv(dotenv_path=_backend_dir / ".env")
    api_key = (os.environ.get("ANTHROPIC_API_KEY") or "").strip()
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY is not set")

    client = Anthropic(api_key=api_key)
    response = client.messages.create(
        model=model or DEFAULT_MODEL,
        max_tokens=max_tokens,
        temperature=temperature,
        system=system,
        messages=[{"role": "user", "content": user}],
    )

    if not response.content or not response.content[0].text:
        raise RuntimeError("Anthropic returned empty response")
    return response.content[0].text.strip()


def parse_json_response(raw: str) -> dict[str, Any]:
    """
    Parse JSON from the response. Strips markdown code fences if present.
    Raises ValueError if no valid JSON found.
    """
    raw = raw.strip()
    if raw.startswith("```"):
        lines = raw.split("\n")
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        raw = "\n".join(lines)
    return json.loads(raw)


def complete_json(
    system: str,
    user: str,
    *,
    model: str | None = None,
    max_tokens: int = MAX_OUTPUT_TOKENS,
    temperature: float = TEMPERATURE,
) -> dict[str, Any]:
    """Call Anthropic (Claude) and return parsed JSON. Raises if output is not valid JSON."""
    raw = complete(
        system=system,
        user=user,
        model=model,
        max_tokens=max_tokens,
        temperature=temperature,
    )
    return parse_json_response(raw)


def get_prompt(name: str, version: str = "v1") -> str:
    """Public helper to load a prompt by name and optional version."""
    return _load_prompt(name, version)
