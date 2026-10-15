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
        return await self._request("GET", path, params)

    async def _request(self, method: str, path: str, params: dict | None = None, ok: tuple[int, ...] = ()) -> httpx.Response:
        try:
            async with httpx.AsyncClient(timeout=30 if method == "POST" else 10) as client:
                resp = await client.request(method, f"{self.base}{path}", params=params)
        except httpx.HTTPError as exc:
            raise DockerError(f"Docker API unreachable: {exc}") from exc
        if resp.status_code in ok:
            return resp
        if resp.status_code == 404:
            raise DockerError("Container not found")
        if resp.status_code == 403 and method == "POST":
            raise DockerError("Container actions are disabled on the Docker socket proxy (set DOCKER_PROXY_ALLOW_ACTIONS=1 and recreate docker-proxy)")
        if resp.status_code >= 400:
            raise DockerError(f"Docker API returned HTTP {resp.status_code} (is the socket proxy allowing CONTAINERS=1?)")
        return resp

    async def list_containers(self) -> list[dict]:
        """Allow-listed containers with basic state (names only; never environment variables)."""
        if not self.enabled:
            return []
        out = []
        for c in (await self._get("/containers/json", {"all": "true"})).json():
            for n in c.get("Names", []):
                n = n.lstrip("/")
                if self._allowed(n):
                    out.append({"name": n, "image": c.get("Image"), "state": c.get("State"), "status": c.get("Status")})
        return sorted(out, key=lambda x: x["name"])

    async def read_logs(self, name: str, tail: int) -> str:
        if not self.enabled or not self._allowed(name) or name not in await self.allowed_names():
            raise DockerError("Container is not in the allow-list")
        info = (await self._get(f"/containers/{name}/json")).json()
        tty = bool((info.get("Config") or {}).get("Tty"))
        resp = await self._get(f"/containers/{name}/logs", {"stdout": "true", "stderr": "true", "tail": str(max(1, min(tail, 2000))), "timestamps": "true"})
        return redact(_demux(resp.content) if not tty else resp.content.decode("utf-8", "replace"))

    async def action(self, name: str, action: str) -> None:
        """start | stop | restart. Only ever invoked from an explicit, permission-checked click in the UI - never by the assistant."""
        if action not in ("start", "stop", "restart"):
            raise DockerError("Unsupported action")
        if not self.enabled or not self._allowed(name) or name not in await self.allowed_names():
            raise DockerError("Container is not in the allow-list")
        params = {"t": "10"} if action in ("stop", "restart") else None
        await self._request("POST", f"/containers/{name}/{action}", params, ok=(204, 304))

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

    async def match_in_text(self, text: str, only: list[str] | None = None) -> tuple[list[str], list[str]]:
        """Returns (containers mentioned in text that the caller may read, container-looking names mentioned but NOT permitted).

        `only` narrows the globally allow-listed containers to those a specific user may access."""
        allowed = await self.allowed_names()
        if only is not None:
            allowed = [n for n in allowed if n in only]
        found = [n for n in allowed if re.search(rf"(?<![\w.-]){re.escape(n)}(?![\w.-])", text, flags=re.I)]
        refused: list[str] = []
        for m in re.finditer(r"(?:container|کانتینر)\s+[`'\"]?([A-Za-z0-9][\w.-]{1,62})", text, flags=re.I):
            cand = m.group(1)
            if cand not in found and cand.lower() not in {"is", "was", "the", "x", "logs", "log", "status"}:
                refused.append(cand)
        return found, refused[:3]

    async def summary(self, name: str) -> dict:
        """State of one container (no logs, never environment variables)."""
        if not self.enabled or not self._allowed(name) or name not in await self.allowed_names():
            raise DockerError("Container is not in the allow-list")
        info = (await self._get(f"/containers/{name}/json")).json()
        return self._summary(name, info)

    async def stats(self, name: str) -> dict:
        """One CPU / memory / network / pids snapshot of a running container."""
        if not self.enabled or not self._allowed(name) or name not in await self.allowed_names():
            raise DockerError("Container is not in the allow-list")
        d = (await self._get(f"/containers/{name}/stats", {"stream": "false", "one-shot": "true"})).json()
        cpu, pre = d.get("cpu_stats", {}), d.get("precpu_stats", {})
        cpu_delta = cpu.get("cpu_usage", {}).get("total_usage", 0) - pre.get("cpu_usage", {}).get("total_usage", 0)
        sys_delta = cpu.get("system_cpu_usage", 0) - pre.get("system_cpu_usage", 0)
        ncpu = cpu.get("online_cpus") or len(cpu.get("cpu_usage", {}).get("percpu_usage") or []) or 1
        mem = d.get("memory_stats", {})
        cache = (mem.get("stats") or {}).get("inactive_file", (mem.get("stats") or {}).get("cache", 0))
        used = max(0, mem.get("usage", 0) - cache)
        limit = mem.get("limit", 0)
        nets = d.get("networks") or {}
        return {
            "name": name,
            "cpu_percent": round(cpu_delta / sys_delta * ncpu * 100, 2) if sys_delta > 0 and cpu_delta >= 0 else None,
            "memory_used_mb": round(used / 1048576, 1),
            "memory_limit_mb": round(limit / 1048576, 1) if limit else None,
            "memory_percent": round(used / limit * 100, 2) if limit else None,
            "net_rx_mb": round(sum(n.get("rx_bytes", 0) for n in nets.values()) / 1048576, 2),
            "net_tx_mb": round(sum(n.get("tx_bytes", 0) for n in nets.values()) / 1048576, 2),
            "pids": (d.get("pids_stats") or {}).get("current"),
        }

    def _summary(self, name: str, info: dict) -> dict:
        state, cfg = info.get("State", {}), info.get("Config", {})
        health = state.get("Health") or {}
        return {
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
