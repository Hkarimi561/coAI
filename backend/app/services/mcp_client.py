"""MCP client: discover and call tools on admin-registered remote servers (streamable HTTP or SSE).

Only tools on the admin allow-list (McpServer.enabled_tools of enabled servers) are ever exposed to the model or callable.
"""

import asyncio
import logging
import re
import time
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Any

from mcp import ClientSession
from mcp.client.sse import sse_client
from mcp.client.streamable_http import streamablehttp_client
from sqlalchemy import select

from app.db import SessionLocal
from app.models import McpServer
from app.security import create_mcp_token

log = logging.getLogger(__name__)

DISCOVER_TIMEOUT_S = 25
CALL_TIMEOUT_S = 45
MAX_RESULT_CHARS = 6000


@asynccontextmanager
async def _open(server: McpServer, user_token: str | None = None):
    headers = dict(server.headers or {})
    if user_token and getattr(server, "forward_user", False):
        headers["X-Coai-User"] = user_token  # per-user permissions are enforced by the MCP server itself
    cm = sse_client(server.url, headers=headers) if server.transport == "sse" else streamablehttp_client(server.url, headers=headers)
    async with cm as streams:
        async with ClientSession(streams[0], streams[1]) as session:
            await session.initialize()
            yield session


async def discover(server: McpServer) -> list[dict[str, Any]]:
    """Connects and lists the tools the server offers."""
    out: list[dict[str, Any]] = []
    async with asyncio.timeout(DISCOVER_TIMEOUT_S):
        async with _open(server) as session:
            cursor = None
            for _ in range(10):  # follow pagination
                res = await session.list_tools(cursor=cursor) if cursor else await session.list_tools()
                out.extend(
                    {
                        "name": t.name, "description": (t.description or "")[:1000], "input_schema": t.inputSchema or {"type": "object", "properties": {}},
                        # tools that change state (destructiveHint) are only offered to the model on an explicit /command
                        "destructive": bool(getattr(getattr(t, "annotations", None), "destructiveHint", None)),
                    }
                    for t in res.tools
                )
                cursor = getattr(res, "nextCursor", None)
                if not cursor:
                    break
    return out


async def _call(server: McpServer, tool: str, args: dict[str, Any], user_token: str | None = None) -> tuple[bool, str]:
    async with asyncio.timeout(CALL_TIMEOUT_S):
        async with _open(server, user_token) as session:
            result = await session.call_tool(tool, args)
    parts: list[str] = []
    for c in result.content:
        text = getattr(c, "text", None)
        parts.append(text if isinstance(text, str) else f"[non-text content: {getattr(c, 'type', 'unknown')}]")
    return not result.isError, "\n".join(parts)[:MAX_RESULT_CHARS]


@dataclass(frozen=True)
class ToolDef:
    alias: str  # name shown to the model: <server>__<tool>
    server_id: str
    server_name: str
    tool: str
    description: str
    schema: dict[str, Any]
    destructive: bool = False  # changes state: offered to the model only when the user types an explicit command

    def openai(self) -> dict[str, Any]:
        return {
            "type": "function",
            "function": {"name": self.alias, "description": f"[MCP server: {self.server_name}] {self.description}"[:900], "parameters": self.schema},
        }


def alias_of(server_name: str, tool: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_-]", "_", f"{server_name}__{tool}")[:64]


_cache: tuple[float, list[ToolDef]] = (0.0, [])


def invalidate() -> None:
    global _cache
    _cache = (0.0, [])


async def enabled_tools() -> list[ToolDef]:
    """Allow-listed tools of enabled servers (cached for a few seconds)."""
    global _cache
    ts, cached = _cache
    if time.monotonic() - ts < 10:
        return cached
    async with SessionLocal() as session:
        servers = (await session.execute(select(McpServer).where(McpServer.enabled.is_(True)))).scalars().all()
    defs: list[ToolDef] = []
    for s in servers:
        allowed = set(s.enabled_tools or [])
        for t in s.tools or []:
            if t["name"] in allowed:
                defs.append(ToolDef(alias_of(s.name, t["name"]), str(s.id), s.name, t["name"], t.get("description", ""), t.get("input_schema") or {"type": "object", "properties": {}}, bool(t.get("destructive"))))
    _cache = (time.monotonic(), defs)
    return defs


async def execute(alias: str, args: dict[str, Any], user_id: str | None = None) -> tuple[ToolDef | None, bool, str, int]:
    """Runs an allow-listed tool as the given user. Returns (tool, ok, text, duration_ms); never raises."""
    t0 = time.monotonic()
    tool = next((d for d in await enabled_tools() if d.alias == alias), None)
    if tool is None:
        return None, False, f"Tool '{alias}' is not available.", 0
    try:
        async with SessionLocal() as session:
            server = await session.get(McpServer, tool.server_id)
        if server is None or not server.enabled:
            return tool, False, "MCP server is disabled.", 0
        token = create_mcp_token(user_id) if (user_id and server.forward_user) else None
        ok, text = await _call(server, tool.tool, args if isinstance(args, dict) else {}, token)
    except Exception as exc:  # noqa: BLE001
        log.warning("MCP tool %s failed: %s", alias, exc)
        return tool, False, f"Tool call failed: {type(exc).__name__}: {str(exc)[:300]}", int((time.monotonic() - t0) * 1000)
    return tool, ok, text, int((time.monotonic() - t0) * 1000)
