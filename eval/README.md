# Answer-quality evaluation

Runs a fixed set of questions through the **same workflow as chat** and prints metrics, so changes to the model, chunking,
embeddings or thresholds can be compared with numbers instead of impressions.

```bash
# copy the question set into the container and run (web search is OFF by default, so runs are repeatable)
docker compose run --rm -v ./eval:/eval backend python -m app.cli eval --dataset /eval/questions.json --out /eval/baseline.json

# no LLM needed: where would each question be answered from? (fast, good for chunking / embedding changes)
docker compose run --rm -v ./eval:/eval backend python -m app.cli eval --dataset /eval/questions.json --retrieval-only

# how does DOC_SUFFICIENCY_SCORE change docs-vs-web decisions?
docker compose run --rm -v ./eval:/eval backend python -m app.cli eval --dataset /eval/questions.json --sweep

# after a change, compare with the earlier report
docker compose run --rm -v ./eval:/eval backend python -m app.cli eval --dataset /eval/questions.json --out /eval/new.json --baseline /eval/baseline.json
```

Options: `--judge` (an LLM compares each answer with the question's `reference`), `--web` (allow live web search),
`--only id1 id2` (run a few questions). The exit code is 1 when any question fails its checks, so it can run in CI.

## Question format

| field | meaning |
|---|---|
| `id`, `question` | required; ids are unique |
| `expect_docs` | substrings of doc paths that must be among the retrieved chunks |
| `expected_stage` | `local_docs`, `solutions`, `web` or `any`: where the answer should come from |
| `must_contain_all` / `must_contain_any` / `must_not_contain` | phrase checks on the answer (case-insensitive) |
| `reference` | reference answer, used only with `--judge` |

## Metrics

| metric | meaning |
|---|---|
| `answered_from_docs_pct`, `..._solutions_...`, `..._web_cache_...` | share of questions whose main source was that stage |
| `reached_web_pct` | share that went to stage 3 (counted even when web search is disabled) |
| `doc_hit_pct` | of the questions with `expect_docs`, how many retrieved the expected document |
| `stage_correct_pct` | of the questions with an `expected_stage`, how many came from it |
| `checks_pass_pct` | phrase checks passed (full runs only) |
| `judge_correct_pct` | LLM judge verdict (only with `--judge`) |

The runs do not write conversations, feedback or analytics, bypass the answer cache and (by default) never leave the network.
`questions.json` is a starter set built from the sample runbooks in `docs/`; replace it with real questions from your team.
