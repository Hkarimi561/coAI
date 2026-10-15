"""Registers the built-in Docker MCP server once (admins can then edit, disable or delete it)."""

import asyncio
import logging

from sqlalchemy import select

from app.config import get_settings
from app.db import SessionLocal
from app.models import AppSetting, McpServer
from app.services import mcp_client

log = logging.getLogger(__name__)
_FLAG = "docker_mcp_seeded"
DESCRIPTION = "مدیریت کانتینرها: وضعیت، لاگ، منابع مصرفی، شروع، توقف و ری‌استارت — بر اساس دسترسی هر کاربر"


async def ensure_docker_server() -> None:
    url = get_settings().docker_mcp_url
    if not url:
        return
    for attempt in range(1, 9):  # the docker-mcp container may still be starting
        try:
            async with SessionLocal() as session:
                if await session.get(AppSetting, _FLAG) is not None:
                    return  # registered before (maybe deleted on purpose by an admin): never re-create
                server = (await session.execute(select(McpServer).where(McpServer.name == "docker"))).scalar_one_or_none()
                if server is None:
                    server = McpServer(name="docker", description=DESCRIPTION, transport="http", url=url, headers={}, forward_user=True,
                                       enabled=True, tools=[], enabled_tools=[])
                    server.tools = await mcp_client.discover(server)
                    server.enabled_tools = [t["name"] for t in server.tools]  # every tool is gated per user by the MCP server itself
                    session.add(server)
                session.add(AppSetting(key=_FLAG, value=True))
                await session.commit()
                mcp_client.invalidate()
                log.info("Registered the built-in Docker MCP server (%d tools)", len(server.tools))
                return
        except Exception as exc:  # noqa: BLE001
            log.warning("Docker MCP registration attempt %d failed: %s", attempt, exc)
            await asyncio.sleep(8 * attempt)
