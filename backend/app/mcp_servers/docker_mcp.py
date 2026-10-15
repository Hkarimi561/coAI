"""Docker MCP server (streamable HTTP, port 9101): container status, logs, stats and start / stop / restart.

Every call is limited by the *calling user's* container permissions (the same grants the admin manages under
"دسترسی کانتینرها"): no grant -> the container does not exist for that user. The backend identifies the user with a short-lived
signed token in the `X-Coai-User` header; calls without a valid token are refused.

State-changing tools carry `destructiveHint=True`; the app only offers them to the model when the user explicitly types a
command such as `/docker restart nginx` (never in free chat).
"""

import fnmatch
import json
import logging
import re

from mcp.server.fastmcp import Context, FastMCP
from mcp.server.fastmcp.exceptions import ToolError
from mcp.types import ToolAnnotations

from app.config import get_settings
from app.db import SessionLocal
from app.models import ContainerAudit, User
from app.redaction import redact
from app.redis_client import rate_limit
from app.security import decode_mcp_token
from app.services import container_access
from app.services.docker_inspector import DockerError, get_docker
from app.textnorm import truncate_middle

log = logging.getLogger(__name__)
mcp = FastMCP(
    "docker",
    host="0.0.0.0",
    port=9101,
    instructions="Inspect and manage Docker containers the current user has been granted access to.",
)

_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,63}$")
_READ = ToolAnnotations(readOnlyHint=True, destructiveHint=False, idempotentHint=True, openWorldHint=False)
_ACT = ToolAnnotations(readOnlyHint=False, destructiveHint=True, idempotentHint=False, openWorldHint=False)


async def _caller(ctx: Context) -> User:
    request = ctx.request_context.request
    token = request.headers.get("x-coai-user") if request is not None else None
    if not token:
        raise ToolError("No user identity was provided; this server must be called through the assistant.")
    try:
        user_id, _role = decode_mcp_token(token)
    except Exception:  # noqa: BLE001
        raise ToolError("The user identity is invalid or expired.") from None
    async with SessionLocal() as s:
        user = await s.get(User, user_id)
    if user is None or not user.is_active:
        raise ToolError("The user is disabled.")
    return user


async def _level(user: User, name: str) -> str | None:
    async with SessionLocal() as s:
        return (await container_access.access_map(s, user, [name])).get(name)


async def _need(user: User, name: str, needed: str) -> None:
    """Raises unless `user` may `needed` ('logs' = read, 'actions' = also start/stop/restart) this container."""
    if not get_docker().enabled:
        raise ToolError("Docker access is not enabled (DOCKER_ALLOWED_CONTAINERS is empty).")
    if not _NAME.match(name):
        raise ToolError("Invalid container name.")
    level = await _level(user, name)
    if not container_access.allows(level, needed):
        # do not reveal containers the user cannot see
        if needed == "actions" and level:
            raise ToolError(f"You may view '{name}' but you do not have permission to run actions on it. Ask an admin for 'actions' access.")
        raise ToolError(f"Container '{name}' was not found or you have no access to it.")


def _protected(name: str) -> bool:
    return any(fnmatch.fnmatch(name, p) for p in get_settings().docker_protected_list)


async def _audit(user: User, name: str, action: str, result: str) -> None:
    async with SessionLocal() as s:
        s.add(ContainerAudit(user_id=user.id, container=name, action=f"mcp:{action}"[:16], result=result[:300]))
        await s.commit()


@mcp.tool(annotations=_READ)
async def list_containers(ctx: Context) -> str:
    """List the containers you can access, with their state, status, image and your access level (logs or actions)."""
    user = await _caller(ctx)
    docker = get_docker()
    if not docker.enabled:
        raise ToolError("Docker access is not enabled (DOCKER_ALLOWED_CONTAINERS is empty).")
    try:
        containers = await docker.list_containers()
    except DockerError as exc:
        raise ToolError(str(exc)) from exc
    async with SessionLocal() as s:
        access = await container_access.access_map(s, user, [c["name"] for c in containers])
    rows = [c for c in containers if c["name"] in access]
    if not rows:
        return "You have no access to any container. Ask an admin to grant access."
    lines = [f"{c['name']} | {c['state']} | {c['status']} | image: {c['image']} | access: {access[c['name']]}" for c in rows]
    return f"{len(rows)} container(s):\n" + "\n".join(lines)


@mcp.tool(annotations=_READ)
async def container_status(name: str, ctx: Context) -> str:
    """Detailed state of one container: running/exited, exit code, OOM kill, restart count, health checks, start/finish times."""
    user = await _caller(ctx)
    await _need(user, name, "logs")
    try:
        info = await get_docker().summary(name)
    except DockerError as exc:
        raise ToolError(str(exc)) from exc
    return json.dumps(info, ensure_ascii=False, indent=2)


@mcp.tool(annotations=_READ)
async def container_logs(name: str, ctx: Context, tail: int = 100) -> str:
    """Last lines of a container's logs (secrets are redacted). `tail` is the number of lines (max 300)."""
    user = await _caller(ctx)
    await _need(user, name, "logs")
    try:
        logs = await get_docker().read_logs(name, max(1, min(tail, 300)))
    except DockerError as exc:
        raise ToolError(str(exc)) from exc
    return truncate_middle(redact(logs), 8000) or "(no log output)"


@mcp.tool(annotations=_READ)
async def container_stats(name: str, ctx: Context) -> str:
    """Current CPU, memory, network and process usage of a running container (one snapshot)."""
    user = await _caller(ctx)
    await _need(user, name, "logs")
    try:
        return json.dumps(await get_docker().stats(name), ensure_ascii=False, indent=2)
    except DockerError as exc:
        raise ToolError(str(exc)) from exc


async def _act(ctx: Context, name: str, action: str) -> str:
    user = await _caller(ctx)
    try:
        await _need(user, name, "actions")
    except ToolError as exc:
        await _audit(user, name, action, "denied")
        raise exc
    if _protected(name):
        await _audit(user, name, action, "denied: protected")
        raise ToolError(f"'{name}' is a protected core container of this platform; it cannot be {action}ed from chat.")
    try:
        await rate_limit(f"cact:{user.id}", 10, 60)
        await get_docker().action(name, action)
    except DockerError as exc:
        await _audit(user, name, action, f"error: {exc}")
        raise ToolError(str(exc)) from exc
    except Exception as exc:  # noqa: BLE001 - e.g. HTTP 429 from the rate limiter
        await _audit(user, name, action, f"error: {type(exc).__name__}")
        raise ToolError("Too many container actions, try again in a minute.") from exc
    await _audit(user, name, action, "ok")
    return f"OK: container '{name}' {action} completed."


@mcp.tool(annotations=_ACT)
async def restart_container(name: str, ctx: Context) -> str:
    """Restart a container (needs 'actions' access). The service is briefly unavailable."""
    return await _act(ctx, name, "restart")


@mcp.tool(annotations=_ACT)
async def stop_container(name: str, ctx: Context) -> str:
    """Stop a running container (needs 'actions' access). The service stays down until it is started again."""
    return await _act(ctx, name, "stop")


@mcp.tool(annotations=_ACT)
async def start_container(name: str, ctx: Context) -> str:
    """Start a stopped container (needs 'actions' access)."""
    return await _act(ctx, name, "start")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    mcp.run(transport="streamable-http")
