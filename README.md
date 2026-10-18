# DevOps AI Assistant (internal)

A Persian-first (RTL) internal chat application for a DevOps team. It answers infrastructure questions and troubleshoots pasted errors from **your own approved Markdown runbooks first**, falls back to **previously confirmed solutions and cached web research**, and only then performs a **live web search** — with durable caching and single-flight locking so the same problem is never searched twice. Users confirm or reject each answer; admins review conversations and promote solved ones into the approved documentation.

```
 Browser ──► Next.js (RTL UI, TanStack Query, Recharts)
               │  /api/* (rewrite, SSE streaming)
               ▼
            FastAPI ──► PostgreSQL   conversations, messages, tool calls, feedback, solutions, web cache, analytics events
               │   ├──► Redis        rate limits · web-cache hot layer · single-flight locks
               │   ├──► Qdrant       vectors: docs · confirmed solutions · web-cache entries
               │   ├──► LLM          Ollama / any OpenAI-compatible server (default qwen3.5:4b)
               │   ├──► SearXNG      (or Tavily)  live web search, last resort
               │   ├──► docker-socket-proxy   read-only: inspect + logs --tail, allow-listed containers
               │   └──► GitHub Actions adapter   latest build/deploy status (optional)
```

## Quick start

Requirements: Docker + Docker Compose v2, and a local LLM server (see [Connect your local Qwen model](#connect-your-local-qwen-model)).

```bash
cp .env.example .env
# edit .env: JWT_SECRET, POSTGRES_PASSWORD, ADMIN_EMAIL / ADMIN_PASSWORD, LLM_*
docker compose up -d --build
docker compose logs -f backend      # wait for "Startup indexing: ..."
```

Open <http://localhost:3000> and sign in with `ADMIN_EMAIL` / `ADMIN_PASSWORD`. The 6 sample runbooks in `./docs` are indexed automatically on start.

The first backend start downloads the embedding model (`intfloat/multilingual-e5-small`, ~470 MB) into the `hf_cache` volume; startup indexing retries until it is ready.

### Create admins / users

* Seed: `ADMIN_EMAIL` + `ADMIN_PASSWORD` in `.env` create the first admin on startup if the e-mail does not exist.
* CLI (also resets the password of an existing user and makes them admin):
  ```bash
  docker compose exec backend python -m app.cli create-admin --email you@company.com --name "Your Name"
  ```
* Admin UI → *Users* creates further users/admins and can disable accounts. There is no public registration.

### Index documentation

Put Markdown files anywhere under `./docs` (mounted at `/data/docs`), then either press **Index changes** in *Admin → Documents* or:

```bash
docker compose exec backend python -m app.cli ingest            # only new/modified files (content hash)
docker compose exec backend python -m app.cli ingest --force    # everything
```

Files can also be uploaded or authored in the admin UI. Deleted files are removed from Qdrant on the next sync. Chunking splits on headings (`Title > H2 > H3` is kept as the chunk heading), packs paragraphs up to `CHUNK_MAX_CHARS` and **never splits a fenced code block**. Each point stores `filename, path, heading, hash, indexed_at`.

## Connect your local Qwen model

**Ollama (default)**

1. Install Ollama on the machine that has the GPU/CPU you want to use, then pull the model:
   ```bash
   ollama pull qwen3.5:4b        # use the exact tag that `ollama list` / the Ollama library shows
   ```
2. Make Ollama reachable from containers. On Linux/macOS/Windows set `OLLAMA_HOST=0.0.0.0` (so it does not bind only to 127.0.0.1) and restart Ollama.
3. In `.env`:
   ```env
   LLM_PROVIDER=ollama
   LLM_BASE_URL=http://host.docker.internal:11434
   LLM_MODEL=qwen3.5:4b
   ```
   `host.docker.internal` works on Docker Desktop; on Linux the compose file maps it with `host-gateway`.
4. `docker compose up -d backend` and ask a question.

**LM Studio** (OpenAI-compatible, default port 1234)

1. In LM Studio load the model, open the *Developer* tab, start the server and enable **Serve on Local Network** (otherwise it only listens on localhost and Docker cannot reach it).
2. In `.env` use the address Docker can reach (your host IP, e.g. `172.19.240.1`, or `host.docker.internal`):
   ```env
   LLM_PROVIDER=openai
   LLM_BASE_URL=http://172.19.240.1:1234/v1
   LLM_MODEL=<model id exactly as LM Studio lists it>
   ```
3. `docker compose up -d backend` and check *Admin → System status* (the header also shows the LLM connection). If the model name is wrong the status page lists the ids the server offers.
4. Optional: if you also load an embedding model in LM Studio, use it instead of the local torch model: `EMBEDDING_PROVIDER=openai`, `EMBEDDING_MODEL=<embedding model id>` (it reuses `LLM_BASE_URL`), `INSTALL_LOCAL_EMBEDDINGS=false`.

**Any OpenAI-compatible server** (llama.cpp `llama-server`, vLLM, LM Studio, Ollama's `/v1`):

```env
LLM_PROVIDER=openai
LLM_BASE_URL=http://host.docker.internal:8081/v1     # must include /v1
LLM_MODEL=qwen3.5-4b-instruct
LLM_API_KEY=                                          # only if the server requires one
```

Notes: `<think>…</think>` blocks are always stripped from the stream. `LLM_THINK=true` enables thinking for Ollama reasoning models (slower). `LLM_NUM_CTX` (default 8192) must be large enough for context + logs; container logs are capped at ~6k characters.

**Embeddings** default to the local `intfloat/multilingual-e5-small` model (CPU, inside the backend container; e5 `query:`/`passage:` prefixes are applied automatically). To skip the large torch install use Ollama/OpenAI embeddings:

```env
INSTALL_LOCAL_EMBEDDINGS=false
EMBEDDING_PROVIDER=ollama          # or openai
EMBEDDING_MODEL=bge-m3
```

> The vector dimension is fixed per collection. If you change the embedding model use a new `QDRANT_COLLECTION` (the backend refuses to start indexing against a mismatching collection) and re-index.

## How an answer is produced

For every user message the backend runs an explicit state machine (`backend/app/services/workflow.py`):

| Step | What happens |
|------|--------------|
| `gather_tools` | Allow-listed Docker containers named in the message are inspected (state, exit code, OOM, restarts, health) and `logs --tail N` is read. "latest build/deploy" questions query the CI adapter. Everything is secret-redacted. Unavailable tools produce a note, not a failure. |
| `plan_queries` | Builds a normalised **error signature** (timestamps, UUIDs, IPs, long numbers, hex ids stripped; key error lines hashed) and the retrieval/web queries. |
| `retrieve_local` | **Stage 1** – approved Markdown chunks in Qdrant. If best score ≥ `DOC_SUFFICIENCY_SCORE` → answer. |
| `retrieve_cache` | **Stage 2** – exact signature lookup in the web cache, then semantic search over *confirmed solutions* and *cached web research*. Sufficient → answer. |
| `web_search` | **Stage 3** – only now the web. `cache → Redis single-flight lock → provider → store`. Concurrent identical problems trigger **one** outbound search; the others wait and reuse the result. |
| `generate` | The LLM streams an answer with inline citations `[n]`; every context item is shown as a citation (doc section, web URL, Docker/CI source). |

**Human-in-the-loop.** After an answer the user presses **Problem solved** or **Encountered an error**.

* *Confirmed* → a `solution` candidate is stored (PostgreSQL + vector index), the conversation becomes `pending_review`, and the solution is immediately reusable at Stage 2.
* *Rejected* → the sources behind that answer are excluded for this conversation, the failed attempt is summarised into the next prompt, and the assistant asks for the new error/output. The next message runs the whole pipeline again with the new context (docs → cache → web only if still needed).

**Admin.** *Admin → Conversations* (search, status filter, pagination) → *Inspector* shows messages, citations, every tool call with input/output and timings, feedback and candidate solutions. **Promote to Documentation** drafts a `Title / Symptoms / Root Cause / Resolution Steps / Verification` Markdown document from the conversation (LLM with a deterministic template fallback), opens the editor with live preview, and on approval writes `docs/promoted/<slug>.md` (with front matter), indexes it into Qdrant, marks the solution `promoted` and the conversation `resolved`.

**Analytics** (*Admin → Dashboard*) are computed from the database: conversations & resolution rate, daily volume, source distribution (local docs / confirmed solutions / web cache / fresh web / Docker / CI), web searches performed vs avoided and cache hit rate, status split, and the top recurring error signatures. *Admin → Web cache* lists entries and lets you invalidate them manually.

## Knowledge gaps and evaluation

* *Admin → Knowledge gaps* clusters the questions the assistant could not answer well. **Draft runbook** on a topic asks the LLM for a runbook (`Symptoms / Root Cause / Resolution Steps / Verification`) from the recurring questions, the assistant's earlier answers and any confirmed solutions; the draft opens in the editor, is marked as unverified, and is only published (and indexed) when an admin approves it. Needs `gaps.view` and `documents.manage`.
* `eval/` holds a question set and `python -m app.cli eval` runs it through the real workflow: share of answers from docs / solutions / web, expected-document hit rate, phrase checks, an optional LLM judge, `--retrieval-only` (no LLM) and `--sweep` (how `DOC_SUFFICIENCY_SCORE` trades docs against web). See [eval/README.md](eval/README.md).

## Admin settings (no restart needed)

*Admin → Settings* switches, applied immediately: **live web search** (SearXNG/Tavily) on/off, **GitHub project docs** on/off, **chat answer cache** on/off. With web search off no request leaves the network except (if enabled) to GitHub; previously cached research is still used. The header and *System status* page show the current state.

## Project documentation from GitHub

When local sources are insufficient (or you ask to search the web) the assistant also reads the documentation of the projects you mention, straight from GitHub, and cites the file URLs: it finds the repositories for the keywords (`angular` → `angular/angular`, `nginx` → `nginx/nginx`; or use a `github.com/owner/repo` link), reads `llms.txt` (from the repo's homepage, e.g. `https://angular.dev/llms.txt`, else the repo root) and follows the linked pages that match the question, then the `README` and the best matching `docs/**/*.md`. The most relevant sections are returned and stored in the normal web cache (same single-flight lock, so a question is researched once). Set `GITHUB_TOKEN` to raise the API rate limit. Fetches from hosts taken from repository metadata are restricted to public HTTPS hosts.

## Teaching the assistant

*Chat → "آموزش به هوش مصنوعی"* opens a **teaching chat**. A team member tells the assistant a procedure/rule; the assistant restates it and asks clarifying questions (no retrieval, nothing executed). When satisfied the user presses **Send for admin review**: the conversation is turned into a lesson (title / when it applies / what to do). Admins review it in *Admin → Lessons* (edit, approve or reject, with the full teaching chat one click away). Only **approved** lessons are indexed and used as high-priority knowledge in answers (cited as "verified lesson"); rejecting an approved lesson removes it again. Users track their lessons under *My lessons*.

## Container access control

`DOCKER_ALLOWED_CONTAINERS` is the outer boundary. Inside it, *Admin → Container access* grants each user, per container (exact name or glob such as `api-*`): **logs** (see state, read logs) or **logs + actions** (also start/stop/restart). Users without a grant cannot see the container at all — neither on the *Containers* page nor through the assistant (the assistant only inspects containers the asking user may read). Admins have full access. Example: user A → `b`, `c` with actions; user D → `c` with logs only.

* Actions happen **only** from a confirmed click on the Containers page, are rate-limited and every attempt (also denied ones) is written to the audit log. The assistant itself still never executes anything.
* Actions additionally require `DOCKER_PROXY_ALLOW_ACTIONS=1` (enables only `start`/`stop`/`restart` on the socket proxy; `docker compose up -d docker-proxy`). Note that the proxy's restart permission also covers `kill`; the backend never calls it.

## Configuration reference

All settings are environment variables (see `.env.example`, which documents every one). Highlights:

| Area | Variables |
|------|-----------|
| Auth | `JWT_SECRET`, `JWT_EXPIRE_HOURS`, `COOKIE_SECURE` (set `true` behind HTTPS), `ADMIN_*` |
| LLM | `LLM_PROVIDER`, `LLM_BASE_URL`, `LLM_MODEL`, `LLM_API_KEY`, `LLM_NUM_CTX`, `LLM_THINK`, `LLM_GRADER_ENABLED` |
| Retrieval | `RETRIEVAL_TOP_K`, `MIN_CONTEXT_SCORE`, `DOC_SUFFICIENCY_SCORE`, `SOLUTION_SUFFICIENCY_SCORE`, `WEB_CACHE_SUFFICIENCY_SCORE` |
| Web search | `WEBSEARCH_PROVIDER=searxng\|tavily\|none`, `TAVILY_API_KEY`, `WEB_CACHE_TTL_HOURS` |
| Docker | `DOCKER_ALLOWED_CONTAINERS` (comma separated names/globs; empty disables), `DOCKER_LOG_TAIL` |
| CI | `CI_PROVIDER=none\|github`, `GITHUB_TOKEN`, `GITHUB_REPO`, `GITHUB_BRANCH` |

**Tuning thresholds.** Cosine scores are model-dependent. If the assistant goes to the web too often, lower `DOC_SUFFICIENCY_SCORE` a little (e5 models score relevant text around 0.80–0.90); if it answers from marginal docs, raise it or set `LLM_GRADER_ENABLED=true`. Each tool call (with its scores) is visible in the Inspector.

**Switch to Tavily:** `WEBSEARCH_PROVIDER=tavily` and `TAVILY_API_KEY=…`. **Disable web search:** `WEBSEARCH_PROVIDER=none` (stages 1–2 still work).

**Docker inspection:**
```env
DOCKER_ALLOWED_CONTAINERS=nginx,api-*,worker
```
The backend never mounts the Docker socket. It talks to `docker-proxy` (tecnativa/docker-socket-proxy) configured with `CONTAINERS=1, POST=0`, so even a compromised backend can only `GET /containers/…`. In code only `GET /containers/json`, `/containers/{name}/json` and `/containers/{name}/logs` are ever called, container names must match the allow-list, and `Config.Env` is never read. If you do not need the feature, remove the `docker-proxy` service.

**GitHub Actions:** `CI_PROVIDER=github`, a token with `actions:read`, `GITHUB_REPO=owner/repo`. Without configuration the assistant tells the user CI status is unavailable and asks for the failing log.

## Security model

* Session = JWT in an `HttpOnly`, `SameSite=Lax` cookie; passwords hashed with bcrypt; login is rate-limited (Redis); chat is rate-limited per user. All `/api/admin/*` routes are guarded server-side by `require_admin`.
* **Secret redaction** (`backend/app/redaction.py`) runs on user input before it is stored, on container logs/CI output before they reach the LLM or the database, on web queries before they leave the network, and on web snippets and model output before storage. Covers bearer tokens, JWTs, cloud/VCS/Slack/API keys, `password=`/`token=`-style assignments, JSON secrets, URLs with credentials, private keys.
* **Prompt-injection defence.** Docs, web results and logs are placed inside `<untrusted_context>` with explicit instructions never to follow commands found there; closing tags in retrieved text are neutralised; the assistant has **no tools that act** — it can only print commands for a human operator. Platform notes are kept in a separate trusted block.
* **No execution.** Nothing in the backend runs shell commands or changes containers. Fix commands are always returned as text for the operator.
* Web queries are built from the normalised, redacted error signature — never from the raw conversation.
* Run behind HTTPS (set `COOKIE_SECURE=true`); put a reverse proxy in front of port 3000. Change every `CHANGE-ME` value.

## Project layout

```
backend/            FastAPI app (app/api, app/services, app/models.py), Alembic migrations, CLI (app/cli.py)
frontend/           Next.js App Router UI (src/app, src/components, src/lib)
docs/               Sample approved runbooks (bind-mounted as the managed docs store)
searxng/            SearXNG settings (JSON output enabled)
docker-compose.yml  postgres · redis · qdrant · searxng · docker-proxy · backend · frontend
```

Migrations run automatically on backend start (`alembic upgrade head`). API docs: <http://localhost:8000/api/docs> (backend port is bound to localhost only).

## Local development without Docker

```bash
# infrastructure only
docker compose up -d postgres redis qdrant searxng

# backend
cd backend && python -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt -r requirements-embeddings.txt
export DATABASE_URL=postgresql+asyncpg://devops:devops@localhost:5432/devops_ai REDIS_URL=redis://localhost:6379/0 \
       QDRANT_URL=http://localhost:6333 SEARXNG_URL=http://localhost:8080 DOCS_DIR=../docs \
       LLM_BASE_URL=http://localhost:11434 DOCKER_HOST=
alembic upgrade head && uvicorn app.main:app --reload

# frontend (BACKEND_URL is baked into the rewrite at build/dev start)
cd frontend && npm install && BACKEND_URL=http://localhost:8000 npm run dev
```
(For the compose `postgres`/`redis`/`qdrant` services to be reachable from the host, add `ports:` mappings in a `docker-compose.override.yml`.)

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| UI shows "⚠️ LLM unavailable" with source list | The backend cannot reach `LLM_BASE_URL`. From `docker compose exec backend python -c "import urllib.request;print(urllib.request.urlopen('<LLM_BASE_URL>/api/tags').read()[:100])"`; make Ollama listen on `0.0.0.0`. |
| Always goes to the web / never finds docs | Check *Admin → Documents* (indexed? chunk count) and lower `DOC_SUFFICIENCY_SCORE`. Inspector → *Tools* shows the scores. |
| Qdrant dimension mismatch error | You changed `EMBEDDING_MODEL`; use a new `QDRANT_COLLECTION` and re-index. |
| SearXNG returns 403 / empty | Make sure `searxng/settings.yml` lists `json` under `search.formats`. |
| Docker inspection says "not in the allow-list" | Add the container name/glob to `DOCKER_ALLOWED_CONTAINERS` and restart the backend. |
| `Permission denied` writing `docs/promoted/…` (Linux) | The backend runs as UID 1000. `sudo chown -R 1000:1000 docs` or rebuild with `APP_UID=$(id -u)`. |
| Chat stream hangs behind a reverse proxy | Disable proxy buffering/gzip for `/api/chat/*` (`proxy_buffering off;`). |

## Scope notes

* **Session memory:** every conversation keeps its own memory (`Conversation.state.memory`): the current problem, a timeline of each answer with its outcome (pending / solved / failed), an LLM-written rolling summary (refreshed in the background after each answer) and a suggested *next step*. It is shown at the top of the chat, injected into the prompt as `<session_memory>`, and used to ground short follow-up questions ("and now what?").
* **Answer cache:** repeated questions are answered instantly from Redis (`ANSWER_CACHE_TTL_HOURS`, default 24h). Not cached: answers built from live Docker/CI data, follow-ups, "no answer" replies, failed searches, rejected answers. Any change to docs, confirmed solutions or the web cache invalidates all cached answers. The **Search again** button (or typing "دوباره جستجو کن") bypasses both caches, runs a real web search and replaces the cached answer.

* **Reasoning output:** the model's thinking (`<think>` blocks, Ollama `thinking`, LM Studio `reasoning_content`) streams into a collapsible panel above each answer and is stored with the message.
* **Theme & direction:** the header has a dark/light toggle (animated circular reveal) and an RTL/LTR switch; both are remembered per browser.

* The workflow is an explicit async state machine (no LangGraph dependency); nodes are small methods and easy to extend.
* Persian fonts: the UI uses the `Vazirmatn` family if installed and falls back to Tahoma/system fonts. Self-host the font in `frontend/public` and add an `@font-face` if you need it everywhere.
* No automated tests are included by request.
