"""Strictly read-only Docker inspection via the Docker Engine API (ideally through a socket proxy).

Only two endpoints are ever called: GET /containers/json, GET /containers/{id}/json and GET /containers/{id}/logs.
Containers must match DOCKER_ALLOWED_CONTAINERS. No exec, no start/stop/restart - ever.
"""

import fnmatch
import logging
import re
import time
from dataclasses import dataclass
from functools import lru_cache

import httpx

from app.config import get_settings
from app.redaction import redact
from app.textnorm import truncate_middle

log = logging.getLogger(__name__)
_NAME_OK = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]*$")


class DockerError(RuntimeError):
    pass


@dataclass
class ContainerSnapshot:
    name: str
    summary: dict
    logs: str


class DockerInspector:
    def __init__(self) -> None:
        s = get_settings()
        self.base = (s.docker_host or "").rstrip("/")
        self.patterns = s.docker_allowlist
        self.tail = s.docker_log_tail
        self._names: list[str] = []
        self._names_at = 0.0

    @property
    def enabled(self) -> bool:
        return bool(self.base and self.patterns)

    def _allowed(self, name: str) -> bool:
        return bool(_NAME_OK.match(name)) and any(fnmatch.fnmatch(name, p) for p in self.patterns)

    async def _get(self, path: str, params: dict | None = None) -> httpx.Response:
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(f"{self.base}{path}", params=params)
        except httpx.HTTPError as exc:
            raise DockerError(f"Docker API unreachable: {exc}") from exc
        if resp.status_code == 404:
            raise DockerError("Container not found")
        if resp.status_code >= 400:
            raise DockerError(f"Docker API returned HTTP {resp.status_code} (is the socket proxy allowing CONTAINERS=1?)")
        return resp

    async def allowed_names(self) -> list[str]:
        if not self.enabled:
            return []
        if time.monotonic() - self._names_at < 30 and self._names:
            return self._names
        resp = await self._get("/containers/json", {"all": "true"})
        names = []
        for c in resp.json():
            for n in c.get("Names", []):
                n = n.lstrip("/")
                if self._allowed(n):
                    names.append(n)
        self._names, self._names_at = sorted(set(names)), time.monotonic()
        return self._names

    async def match_in_text(self, text: str) -> tuple[list[str], list[str]]:
        """Returns (allowed containers mentioned in text, container-looking names mentioned but NOT allowed)."""
        allowed = await self.allowed_names()
        found = [n for n in allowed if re.search(rf"(?<![\w.-]){re.escape(n)}(?![\w.-])", text, flags=re.I)]
        refused: list[str] = []
        for m in re.finditer(r"(?:container|کانتینر)\s+[`'\"]?([A-Za-z0-9][\w.-]{1,62})", text, flags=re.I):
            cand = m.group(1)
            if cand not in found and cand.lower() not in {"is", "was", "the", "x", "logs", "log", "status"}:
                refused.append(cand)
        return found, refused[:3]

    async def snapshot(self, name: str) -> ContainerSnapshot:
        if not self.enabled or not self._allowed(name) or name not in await self.allowed_names():
            raise DockerError("Container is not in the allow-list")
        info = (await self._get(f"/containers/{name}/json")).json()
        state, cfg = info.get("State", {}), info.get("Config", {})
        health = state.get("Health") or {}
        summary = {
            "name": name,
            "image": cfg.get("Image"),
            "status": state.get("Status"),
            "running": state.get("Running"),
            "exit_code": state.get("ExitCode"),
            "oom_killed": state.get("OOMKilled"),
            "restart_count": info.get("RestartCount"),
            "started_at": state.get("StartedAt"),
            "finished_at": state.get("FinishedAt"),
            "error": redact(state.get("Error") or ""),
            "health": health.get("Status"),
            "health_log": [redact(str(h.get("Output", ""))[:300]) for h in (health.get("Log") or [])[-2:]],
        }  # note: Config.Env is deliberately never read - it routinely contains secrets
        tty = bool(cfg.get("Tty"))
        resp = await self._get(
            f"/containers/{name}/logs", {"stdout": "true", "stderr": "true", "tail": str(self.tail), "timestamps": "true"}
        )
        logs = redact(_demux(resp.content) if not tty else resp.content.decode("utf-8", "replace"))
        return ContainerSnapshot(name=name, summary=summary, logs=truncate_middle(logs, 6000))


def _demux(data: bytes) -> str:
    """Docker multiplexes stdout/stderr in 8-byte-header frames for non-TTY containers."""
    if len(data) < 8 or data[0] not in (0, 1, 2) or data[1:4] != b"\x00\x00\x00":
        return data.decode("utf-8", "replace")
    out, i = [], 0
    while i + 8 <= len(data):
        size = int.from_bytes(data[i + 4:i + 8], "big")
        out.append(data[i + 8:i + 8 + size].decode("utf-8", "replace"))
        i += 8 + size
    return "".join(out)


@lru_cache
def get_docker() -> DockerInspector:
    return DockerInspector()
