"""Reads a project's own documentation from GitHub: llms.txt, README and the docs/*.md files that match the question.

For "how do I deploy an angular app with nginx" it finds the angular and nginx repositories, reads their llms.txt (repo
homepage or repo root, following the linked pages that match), README.md and the most relevant Markdown files under docs/,
then returns the best-matching sections together with the GitHub URL of every file.
"""

import asyncio
import base64
import ipaddress
import logging
import re
import socket
from urllib.parse import urljoin, urlparse

import httpx

from app.config import get_settings
from app.redaction import redact
from app.services.chunker import chunk_markdown, parse_document
from app.services.search_types import SearchResult, WebSearchError

log = logging.getLogger(__name__)

_STOP = set(
    "a an the and or of to in on for with from by at as is are was were be been it its this that these those how what why when where which who "
    "can could should would do does did i my me we our you your they them not no yes if then than so very just also please "
    "run runs running start starts bring up set setup install installation use using used deploy deployment configure config configuration "
    "create make project app application apps get got getting error errors problem problems issue issues fix fixes work works working "
    "way best new old simple basic guide tutorial example examples docs doc documentation search find look read".split()
)
_WORD = re.compile(r"[A-Za-z][A-Za-z0-9_.+-]{1,}")
_LINK = re.compile(r"\[([^\]]*)\]\(([^)\s]+)\)")
_GH_URL = re.compile(r"github\.com/([\w.-]+)/([\w.-]+)")
_MAX_BYTES = 300_000


def keywords(query: str) -> list[str]:
    seen: list[str] = []
    for w in _WORD.findall(query):
        w = w.lower().strip(".-_")
        if len(w) >= 3 and w not in _STOP and w not in seen:
            seen.append(w)
    return seen


def _score(text: str, kws: list[str]) -> int:
    t = text.lower()
    return sum(t.count(k) for k in kws)


async def _is_public_https(url: str) -> bool:
    """SSRF guard for hosts that come from repository metadata / llms.txt links."""
    u = urlparse(url)
    if u.scheme != "https" or not u.hostname or u.hostname in ("localhost",) or u.hostname.endswith((".local", ".internal")):
        return False
    try:
        infos = await asyncio.to_thread(socket.getaddrinfo, u.hostname, u.port or 443, type=socket.SOCK_STREAM)
        return bool(infos) and all(ipaddress.ip_address(i[4][0]).is_global for i in infos)
    except (OSError, ValueError):
        return False


class GithubDocsProvider:
    name = "github"

    def __init__(self) -> None:
        s = get_settings()
        self.api = s.github_api_url.rstrip("/")
        self.max_repos = s.github_docs_max_repos
        self.max_files = s.github_docs_max_files
        self.timeout = s.websearch_timeout_s
        self.headers = {"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28", "User-Agent": "devops-ai-assistant"}
        if s.github_token:
            self.headers["Authorization"] = f"Bearer {s.github_token}"

    # ------------------------------------------------------------------ public
    async def search(self, query: str, limit: int) -> list[SearchResult]:
        kws = keywords(query)
        if not kws and not _GH_URL.search(query):
            return []
        async with httpx.AsyncClient(timeout=self.timeout, headers=self.headers, follow_redirects=False) as client:
            repos = await self._find_repos(client, query, kws)
            per_repo: list[list[SearchResult]] = []
            for repo in repos:
                try:
                    per_repo.append(await self._repo_docs(client, repo, kws))
                except httpx.HTTPError as exc:
                    log.warning("GitHub docs for %s failed: %s", repo["full_name"], exc)
        # round-robin so that every repository (angular AND nginx) is represented, best sections first
        results: list[SearchResult] = []
        for i in range(max((len(r) for r in per_repo), default=0)):
            results += [r[i] for r in per_repo if i < len(r)]
        return results[:limit]

    # ------------------------------------------------------------------ repos
    async def _find_repos(self, client: httpx.AsyncClient, query: str, kws: list[str]) -> list[dict]:
        repos: list[dict] = []
        seen: set[str] = set()

        async def add(full_name: str) -> None:
            if full_name.lower() in seen or len(repos) >= self.max_repos:
                return
            r = await client.get(f"{self.api}/repos/{full_name}")
            if r.status_code == 200:
                seen.add(full_name.lower())
                repos.append(r.json())

        try:
            for m in _GH_URL.finditer(query):  # an explicit github.com/owner/repo wins
                await add(f"{m.group(1)}/{m.group(2).removesuffix('.git')}")
            for kw in kws[:4]:
                if len(repos) >= self.max_repos:
                    break
                r = await client.get(f"{self.api}/search/repositories", params={"q": f"{kw} in:name", "sort": "stars", "order": "desc", "per_page": 3})
                if r.status_code in (403, 429):
                    raise WebSearchError("GitHub API rate limit reached (set GITHUB_TOKEN to raise it)")
                if r.status_code != 200:
                    continue
                for item in r.json().get("items", []):
                    if kw in item["name"].lower():  # first (most starred) repository whose NAME contains the keyword
                        if item["full_name"].lower() not in seen and len(repos) < self.max_repos:
                            seen.add(item["full_name"].lower())
                            repos.append(item)
                        break
        except httpx.HTTPError as exc:
            raise WebSearchError(f"GitHub API unreachable: {exc}") from exc
        return repos

    # ------------------------------------------------------------------ files
    async def _get_text(self, client: httpx.AsyncClient, url: str, check_public: bool = False) -> str | None:
        if check_public and not await _is_public_https(url):
            return None
        try:
            r = await client.get(url)
        except httpx.HTTPError:
            return None
        if r.status_code != 200 or len(r.content) > _MAX_BYTES * 3:
            return None
        return r.content[:_MAX_BYTES].decode("utf-8", "replace")

    async def _repo_docs(self, client: httpx.AsyncClient, repo: dict, kws: list[str]) -> list[SearchResult]:
        full, branch = repo["full_name"], repo.get("default_branch") or "main"
        raw = f"https://raw.githubusercontent.com/{full}/{branch}"
        blob = f"https://github.com/{full}/blob/{branch}"
        docs: list[tuple[str, str, str]] = []  # (label, url, text)

        # 1) llms.txt: the project's website first (e.g. https://angular.dev/llms.txt), then the repo root
        homepage = (repo.get("homepage") or "").strip().rstrip("/")
        candidates = ([(f"{homepage}/llms.txt", True)] if homepage.startswith("https://") else []) + [(f"{raw}/llms.txt", False)]
        for url, check in candidates:
            text = await self._get_text(client, url, check_public=check)
            if text and text.strip():
                docs.append(("llms.txt", url, text))
                host = urlparse(url).netloc
                ranked = []
                for label, link in _LINK.findall(text):
                    target = urljoin(url, link.split("#")[0])
                    if urlparse(target).netloc == host and target != url:
                        ranked.append((_score(f"{label} {target}", kws), target, label))
                for sc, target, label in sorted(ranked, key=lambda x: -x[0])[:3]:
                    if sc > 0:
                        body = await self._get_text(client, target, check_public=check)
                        if body:
                            docs.append((label or target.rsplit("/", 1)[-1], target, body))
                break

        # 2) README
        r = await client.get(f"{self.api}/repos/{full}/readme")
        if r.status_code == 200:
            data = r.json()
            try:
                docs.append(("README", data.get("html_url") or f"{blob}/README.md", base64.b64decode(data["content"]).decode("utf-8", "replace")[:_MAX_BYTES]))
            except (KeyError, ValueError):
                pass

        # 3) the Markdown files under docs/ whose path matches the question
        t = await client.get(f"{self.api}/repos/{full}/git/trees/{branch}", params={"recursive": "1"})
        if t.status_code == 200:
            paths = [
                e["path"] for e in t.json().get("tree", [])
                if e.get("type") == "blob" and re.search(r"\.mdx?$", e["path"], re.I) and re.match(r"(?i)(docs?|documentation|guides?|content)/", e["path"])
            ]
            ranked_paths = sorted(((_score(p, kws), p) for p in paths), reverse=True)
            for sc, path in ranked_paths[: self.max_files]:
                if sc <= 0:
                    break
                body = await self._get_text(client, f"{raw}/{path}")
                if body:
                    docs.append((path, f"{blob}/{path}", body))

        scored: list[tuple[float, SearchResult]] = []
        for label, url, text in docs:
            weight = 0.4 if (label == "llms.txt") else 1.0  # the llms.txt root is mostly an index of links
            scored += [(sc * weight, r) for sc, r in self._best_sections(f"{full} — {label}", url, text, kws, label)]
        return [r for _, r in sorted(scored, key=lambda x: -x[0])]

    @staticmethod
    def _best_sections(title: str, url: str, text: str, kws: list[str], label: str) -> list[tuple[float, SearchResult]]:
        parsed = parse_document(text, fallback_title=label)
        chunks = chunk_markdown(parsed.body, parsed.title, 1200) or []
        ranked = sorted(chunks, key=lambda c: -_score(f"{c.heading} {c.heading} {c.text}", kws))
        picked = [c for c in ranked if _score(f"{c.heading} {c.text}", kws) > 0][:2] or (chunks[:1] if label == "README" else [])
        return [
            (float(_score(f"{c.heading} {c.heading} {c.text}", kws)),
             SearchResult(title=f"{title} › {c.heading.split(' > ')[-1]}"[:200], url=url, snippet=redact(c.text)[:1300], source="github"))
            for c in picked
        ]
