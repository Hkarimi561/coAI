"""Slash commands that force an MCP server (or one of its tools): `/server text` or `/server@tool text`."""

import re
from dataclasses import dataclass

from app.services import mcp_client

_CMD = re.compile(r"^\s*/([A-Za-z0-9][A-Za-z0-9_-]{0,47})(?:@([A-Za-z0-9_.:-]{1,64}))?(?:\s+(.*))?$", re.S)


@dataclass(frozen=True)
class McpCommand:
    server: str
    tool: str | None
    text: str  # the request after the command


def parse(message: str) -> McpCommand | None:
    m = _CMD.match(message or "")
    if not m:
        return None
    return McpCommand(m.group(1).lower(), m.group(2), (m.group(3) or "").strip())


async def available() -> list[dict]:
    """Enabled servers with their allow-listed tools (what the autocomplete shows)."""
    out: dict[str, dict] = {}
    for d in await mcp_client.enabled_tools():
        s = out.setdefault(d.server_name, {"server": d.server_name, "tools": []})
        s["tools"].append({"name": d.tool, "description": d.description[:300]})
    return sorted(out.values(), key=lambda s: s["server"])


async def resolve(cmd: McpCommand) -> str | None:
    """Returns an error text (Persian) when the command cannot be run, else None."""
    avail = await available()
    names = ", ".join(f"/{s['server']}" for s in avail) or "—"
    server = next((s for s in avail if s["server"] == cmd.server), None)
    if server is None:
        return f"سرور MCP «{cmd.server}» پیدا نشد یا غیرفعال است.\n\nسرورهای در دسترس: {names}\nبا تایپ `/` فهرست را ببینید."
    if cmd.tool and not any(t["name"] == cmd.tool for t in server["tools"]):
        tools = "، ".join(f"`{t['name']}`" for t in server["tools"])
        return f"ابزار «{cmd.tool}» در سرور «{cmd.server}» فعال نیست.\n\nابزارهای فعال: {tools}"
    if not cmd.text:
        return f"بعد از دستور، درخواست خود را بنویسید. مثال: `/{cmd.server}{'@' + cmd.tool if cmd.tool else ''} درخواست شما`"
    return None
