"""CI adapter interface + GitHub Actions implementation. Read-only."""

import logging
from dataclasses import dataclass, field
from functools import lru_cache
from typing import Protocol

import httpx

from app.config import get_settings
from app.redaction import redact

log = logging.getLogger(__name__)


class CIError(RuntimeError):
    pass


@dataclass
class CIRun:
    id: str
    name: str
    status: str
    conclusion: str | None
    branch: str
    commit: str
    url: str
    created_at: str
    failed: list[str] = field(default_factory=list)  # "job / step" that failed


class CIAdapter(Protocol):
    name: str
    configured: bool

    async def latest_runs(self, limit: int = 5) -> list[CIRun]: ...


class NullCI:
    name = "none"
    configured = False

    async def latest_runs(self, limit: int = 5) -> list[CIRun]:
        raise CIError("No CI provider is configured (set CI_PROVIDER=github, GITHUB_TOKEN and GITHUB_REPO)")


class GitHubActionsCI:
    name = "github"

    def __init__(self) -> None:
        s = get_settings()
        self.configured = bool(s.github_token and s.github_repo)
        self.repo = s.github_repo or ""
        self.base = s.github_api_url.rstrip("/")
        self.branch = s.github_branch
        self.headers = {
            "Authorization": f"Bearer {s.github_token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

    async def _get(self, client: httpx.AsyncClient, path: str, params: dict | None = None) -> dict:
        try:
            resp = await client.get(f"{self.base}{path}", params=params, headers=self.headers)
        except httpx.HTTPError as exc:
            raise CIError(f"GitHub API unreachable: {exc}") from exc
        if resp.status_code >= 400:
            raise CIError(f"GitHub API returned HTTP {resp.status_code}")
        return resp.json()

    async def latest_runs(self, limit: int = 5) -> list[CIRun]:
        if not self.configured:
            raise CIError("GitHub CI adapter is missing GITHUB_TOKEN or GITHUB_REPO")
        params: dict = {"per_page": limit}
        if self.branch:
            params["branch"] = self.branch
        async with httpx.AsyncClient(timeout=15) as client:
            data = await self._get(client, f"/repos/{self.repo}/actions/runs", params)
            runs: list[CIRun] = []
            for r in data.get("workflow_runs", [])[:limit]:
                run = CIRun(
                    id=str(r["id"]), name=r.get("name") or "", status=r.get("status") or "", conclusion=r.get("conclusion"),
                    branch=r.get("head_branch") or "", commit=(r.get("head_sha") or "")[:8],
                    url=r.get("html_url") or "", created_at=r.get("created_at") or "",
                )
                if run.conclusion == "failure" and len([x for x in runs if x.failed]) < 2:
                    jobs = await self._get(client, f"/repos/{self.repo}/actions/runs/{r['id']}/jobs", {"per_page": 30})
                    for job in jobs.get("jobs", []):
                        if job.get("conclusion") == "failure":
                            steps = [st["name"] for st in job.get("steps", []) if st.get("conclusion") == "failure"]
                            run.failed.append(f"{job.get('name')} / {', '.join(steps) or 'unknown step'}")
                runs.append(run)
        return runs


def render_runs(runs: list[CIRun]) -> str:
    lines = []
    for r in runs:
        outcome = r.conclusion or r.status
        lines.append(f"- run #{r.id} '{r.name}' on {r.branch}@{r.commit}: {outcome} ({r.created_at}) {r.url}")
        for f in r.failed:
            lines.append(f"    failed: {f}")
    return redact("\n".join(lines))


@lru_cache
def get_ci() -> CIAdapter:
    return GitHubActionsCI() if get_settings().ci_provider.lower() == "github" else NullCI()
