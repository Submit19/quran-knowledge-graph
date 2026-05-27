# Architecture Audit — Pass 2: Duplication & scattered config (2026-05-22)

Branch: `claude/architecture-audit-2026-05-22`
Scope: repo-wide `*.py` (root + `scripts/` + `eval/v2/`).
Method: grep-based pattern matching for shared signatures, env-var keys, model literals, regex patterns, and Cypher templates; LOC and importer counts via `git`.

> **What I'm flagging vs not.** Duplication is only worth a refactor when consolidating it would (a) prevent a concrete drift bug or (b) materially lower cognitive load. I'm flagging duplications that pass that bar. Duplications that look ugly but are stable (e.g. each `tool_*` function having its own Cypher query) are not flagged here — they belong in Pass 5 strategic suggestions if at all.

---

## TL;DR

- **Five hot duplications** are concrete refactor wins:
  1. `_load_env` helper appears verbatim in 5 files (~65 LOC) — a single `quran_kg.env.load()` collapses it.
  2. **44 files** call `GraphDatabase.driver(NEO4J_URI, ...)` with their own copy of the 4-var env block (~9 LOC × 44 = ~400 LOC of dead-weight). A `quran_kg.neo4j.get_driver()` helper kills it.
  3. **Three citation-extraction regexes** (`shared_agent`, `evaluate`/`autoresearch_local`, `eval_qrcd`) each implement their own `re.compile(r"\[(\d+:\d+)\]")`, while `ref_resolver.py` already has a vastly more complete implementation. None of the three consume `ref_resolver`.
  4. **Three reranker entrypoints** (`model_registry.get_reranker`, `retrieval_gate._get_reranker`, `answer_cache._get_reranker`). `model_registry`'s own docstring acknowledges the migration is incomplete.
  5. **Six `scripts/{audit,enrich,prune,prune_pass2_5,coverage,reembed}_cache*.py` follow the same load → process → `_save_cache` shape** with five copies of the same Path/JSON boilerplate.
- **One scattered env-var surface:** ~44 distinct env vars read across the codebase with no central registry, no validation, no source-of-truth doc beyond the freeform list in `CLAUDE.md`. The risk is silent typos (`RERANKER_MODEL` vs `RERANK_MODEL`, `RERANK_DISABLED` vs `CACHE_RERANK_DISABLED`) and undocumented keys.
- **One residual giant:** `chat.py` is still 2,650 LOC despite Phase 3a's `shared_agent` extraction. The TOOLS JSON schema alone is ~590 LOC. QKG_AUDIT §4 already prescribed the split (`tools/search.py`, `tools/etymology.py`, `tools/code19.py`, `dispatch.py`, `tools/schema.py`).
- **App-variant residual:** after Phase 3a, `app.py` / `app_full.py` / `app_lite.py` are now ~190-280 LOC each but still each carry their own Neo4j init + env load + FastAPI route registration (~90-180 lines between env load and `app = FastAPI()` per file). Phase 3a unified the loop, not the FastAPI surface.

---

## 1 · Verbatim duplication (1-for-1 copy-paste)

### 1a · `_load_env` helper (5 files, ~65 LOC)

The helper appears in `app.py:31-42`, `app_free.py:42-53`, `app_full.py:38-49`, `app_lite.py:38-49`, `chat.py:29-40`. The bodies are character-identical apart from `chat.py` taking an optional `path` argument:

```python
def _load_env():
    path = Path(__file__).parent / ".env"
    if not path.exists():
        return
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1)
                if v.strip():
                    os.environ[k.strip()] = v.strip()
```

It exists because `dotenv` was silently dropping long values (per `chat.py` history). Every file then calls **both** `load_dotenv()` AND `_load_env()` — belt + suspenders. The bug is the helper's reason for existing, but the helper is now 5 copies of the same workaround. **Fix: single `quran_kg.env.load()` (or `bootstrap_env()` if added to `config.py`).**

### 1b · `_BRACKET_REF` citation regex (3+ implementations)

| Site | Pattern | Notes |
|------|---------|-------|
| `evaluate.py:38` | `re.compile(r'\[(\d+:\d+)\]')` | bracketed `[s:v]` only |
| `autoresearch_local.py:73` | `re.compile(r'\[(\d+:\d+)\]')` | verbatim copy of evaluate.py |
| `shared_agent.py:203` | `re.compile(r"(\d+:\d+)")` | unbracketed — **different semantics!** picks up colons in arbitrary text |
| `eval_qrcd.py:88` | (function `extract_citations`) | separate impl |
| `ref_resolver.py:196-242` | 8 different regexes for `[2:255]`, `Quran X:Y`, `Surah Al-Baqarah verse 286`, Arabic forms, etc. | The canonical implementation, already shipping. |

The first 4 are at risk of disagreeing on edge cases. Any code that needs "find verse refs in a string" should call `ref_resolver.resolve_refs(text)` rather than open-code a regex. The audit's "verification eval" and "citation-density retry" both depend on consistent verse extraction; today they may disagree.

### 1c · `cosine` similarity helper (3 implementations)

`classify_edges.py:62`, `consolidate_traces.py:66`, `scripts/cache_coverage_report.py:75` each define their own `cosine` / `_cosine` function over `numpy.dot / linalg.norm`. Two are ~5 lines, one is ~8. Trivial duplication but identical math. Worth one shared helper if a `quran_kg.math` module ever exists.

### 1d · `sys.stdout.reconfigure(encoding="utf-8", errors="replace")` (~31 files)

Windows-specific stdout encoding workaround, copy-pasted with try/except. Could move into a single `bootstrap_io()` call at the top of each script — but the migration is mechanical and the cost of leaving it is low. **Flag, don't urgently fix.**

---

## 2 · Boilerplate duplication (similar structure, varying details)

### 2a · Neo4j driver init across **44 files**

```
$ grep -l "GraphDatabase.driver" --include="*.py" . | wc -l
44
```

Almost every `*.py` (other than the pure helpers `model_registry`, `bullet_dedup`, `tool_compressor`, `sse_pump`, `startup_banner`, `ref_resolver`, `uncertainty`, `config`, the `app_*` wrappers' siblings) re-implements:

```python
URI = os.getenv("NEO4J_URI"); USER = os.getenv("NEO4J_USER")
PASSWORD = os.getenv("NEO4J_PASSWORD"); DB = os.getenv("NEO4J_DATABASE", "quran")
driver = GraphDatabase.driver(URI, auth=(USER, PASSWORD))
driver.verify_connectivity()
```

That's ~6-9 LOC × 44 files ≈ **400 LOC** of identical boilerplate. Defaults drift too: `analyze_graph_structure.py` defaults `NEO4J_PASSWORD` to `""`; `app_*` defaults same; build scripts mostly leave it `None`; one historical script (`backfill_retrieved_model_version.py`) defaults to a literal password — flagged in Pass 1 as a one-shot but the literal is still in the file.

**Fix:** introduce `quran_kg/neo4j_session.py` (or extend `config.py`) with:

```python
def get_driver(): ...   # cached singleton
def session(db: str = "quran"): ...   # context manager
```

44 files → 1 import, ~400 LOC eliminated, defaults centralised.

### 2b · App-variant FastAPI handlers (~600+ LOC residual)

Phase 3a (commits `7b87e5a`, `3f64f22`, `49ee429`) extracted the **agent loop** into `shared_agent.py`. The **FastAPI route surface** was not extracted. Each variant still contains:

| File | Total LOC | Env→FastAPI block | /chat handler at | Distinct routes |
|------|----------:|------------------:|-----------------:|----------------:|
| `app.py` | 191 | line 31→122 (~91) | 165 | 7 |
| `app_free.py` | 506 | line 42→218 (~176) | 420 | 10 |
| `app_full.py` | 209 | line 38→141 (~103) | 183 | 7 |
| `app_lite.py` | 277 | line 38→137 (~99) | 250 | 9 |

`/stats`, `/cache-stats`, `/model-info`, `/verses`, `/chat`, `/`, `/api/resolve_refs`, `/api/verse/{id}`, `/quran_linker.js` — most variants implement nearly identical handlers. The body of `/chat` is now thin (calls `shared_agent.agent_stream`), but the **wrapper around the agent** (Neo4j driver, AgentCollaborators construction, FastAPI mount) is each variant's responsibility.

A second extraction pass could lift these into `shared_app.build_app(config) -> FastAPI` and shrink each variant to ~30-50 LOC of "here's the config, here's the model name, here's whether we wire verification". **Estimate: 400-500 LOC removed across all four wrappers.**

### 2c · `scripts/*cache*.py` follow one shape

Six scripts, all "Pass N over `data/answer_cache.json`":

- `scripts/audit_cache_quality.py` (Pass 1)
- `scripts/prune_cache.py` (Pass 2)
- `scripts/prune_cache_pass2_5.py` (Pass 2.5)
- `scripts/enrich_cache_schema.py` (Pass 3)
- `scripts/reembed_cache_m3.py` (Pass 4)
- `scripts/cache_coverage_report.py` (Pass 5)

They all:

1. `from pathlib import Path; CACHE = Path("data/answer_cache.json")`
2. `cache = json.loads(CACHE.read_text(...))` or `answer_cache._load_cache()`
3. iterate entries, compute / filter / annotate
4. (optionally) `answer_cache._save_cache(cache)` for writers
5. (optionally) append to a `data/research/cache_*_<date>.jsonl` paper trail
6. print a tabular summary + exit

Per-pass logic is distinct (and rightly so), but the framing is identical. The pass scripts are **chained by hand** at the moment — there is no `python scripts/cache_passes.py --pass audit` CLI.

**Fix (also a strategic pass-5 item):**

```python
# scripts/cache_passes/__init__.py
class BasePass:
    name: str
    def filter_or_annotate(self, entry: dict) -> ...
    def summary(self, results) -> str
    def run(self): ...   # shared load + save + paper trail
```

A single `python -m scripts.cache_passes --pass {audit|prune|enrich|reembed|coverage} [--out ...]` CLI would replace the six scripts. The current shape is fine for short-term iteration but will rot if the cache gains more passes.

### 2d · Build-pipeline scripts share `(load_dotenv → env → driver → main → close)` shape

~22 build/import/backfill scripts use the same outline (counts from the file list in §2a). Per-script logic is distinct (each populates a different node type), but the wrapper is identical. The same `quran_kg.neo4j.get_driver()` helper from §2a does most of the work; a one-line context manager finishes it:

```python
def with_driver(fn):
    """Decorator: pass `session` as first arg, manage lifecycle."""
    ...
```

Lower-priority than §2a — the build scripts are write-once and rarely touched — but worth doing in the same refactor wave.

---

## 3 · Three reranker entry points (incomplete migration)

`model_registry.py` was introduced explicitly to centralise heavyweight ML model loading. Its docstring says:

> retrieval_gate.py should call get_reranker() instead of its own _get_reranker() once it migrates; the existing _get_reranker() in retrieval_gate.py is left in place for backward compatibility.

The migration is **not yet done**. Today the call graph is:

```
chat.tool_semantic_search → retrieval_gate.rerank → retrieval_gate._get_reranker → CrossEncoder(...)
answer_cache.search_cache  → answer_cache._get_reranker → retrieval_gate._get_reranker → (same)
[hypothetical new caller]   → model_registry.get_reranker → CrossEncoder(...)  [SEPARATE INSTANCE]
```

Three separate `CrossEncoder` instances are possible if someone calls `model_registry.get_reranker()` while `retrieval_gate._get_reranker()` is already cached. Each is ~600 MB resident. The risk today is small (no one calls `model_registry.get_reranker` for the reranker yet) but the design intent has not been completed.

`RERANKER_MODEL` and `RERANK_DISABLED` are read TWICE (`retrieval_gate.py:31-33` and `model_registry.py:74-79`) — drift candidate.

**Fix:** `retrieval_gate.py::_get_reranker` becomes a thin alias to `model_registry.get_reranker`; same for `answer_cache.py::_get_reranker`. Net: ~20 LOC removed, single instance guaranteed.

---

## 4 · Scattered env-var surface (~44 keys, no registry)

A `grep` for `os.environ.get` / `os.getenv` returns **44 distinct uppercase keys** read across the codebase. `CLAUDE.md` documents the most important ones in two places ("Optional env vars" + scattered usage notes), but there is no machine-readable registry. Risks:

1. **Silent typos.** `RERANK_DISABLED` (used by retrieval_gate, model_registry) vs `CACHE_RERANK_DISABLED` (used by answer_cache) — both legitimate, easily confused.
2. **Default drift.** `RERANKER_MODEL` defaults to `"BAAI/bge-reranker-v2-m3"` in two places. If only one is updated, the other silently keeps the old default.
3. **No `.env.example` validation.** Pass 1 mentioned that `.env.example` is "expanded to cover every key the app reads" (commit `134b173`), but there is no test that asserts every `os.environ.get` key is in `.env.example`.

| Bucket | Count | Sample |
|--------|------:|--------|
| Neo4j | 4 | `NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD`, `NEO4J_DATABASE` |
| LLM credentials | 3 | `ANTHROPIC_API_KEY`, `ANTHROPIC_OAUTH_TOKEN`, `OPENROUTER_API_KEY` |
| Model selection | 6 | `RERANKER_MODEL`, `SEMANTIC_SEARCH_INDEX`, `OPENROUTER_MODEL`, `HAIKU_MODEL`, `EVAL_MODEL`, `DECOMPOSE_MODEL` |
| Tool-call cache | 2 | `TOOL_CACHE_TTL_SEC`, `TOOL_CACHE_MAX` |
| Reranker switches | 2 | `RERANK_DISABLED`, `CACHE_RERANK_DISABLED` |
| Citation verifier | 5 | `ENABLE_CITATION_VERIFY`, `CITATION_VERIFIER_MODEL`, `MINICHECK_MODEL`, `MINICHECK_THRESHOLD`, `CITATION_DECOMPOSE` |
| Ralph / tick scaffold | 7 | `MEMORY_HYGIENE_DISABLED`, `MEMORY_HYGIENE_SKIP_HAIKU`, `HAIKU_PREP_*` (×3), `SONNET_PREP_*` (×2), `RALPH_AGENT_*` (×2) |
| Eval v2 / harness | 5 | `EVAL_LOCAL_ONLY`, `EVAL_PORT`, `EVAL_V2_JUDGE_BACKEND`, `EVAL_V2_JUDGE_MODEL`, `PREFER_OPENROUTER` |
| Misc | 4 | `QURAN_SERVER_PORT`, `PDF_PATH`, … |

**Fix:** a single `env.py` (or extension to `config.py`) with typed `Settings` (Pydantic dataclass or even plain dataclass). Optional but high-leverage: a small `test_env_keys_documented.py` that asserts every `os.environ.get` key in tracked `*.py` is also in `.env.example`.

---

## 5 · `chat.py` is still 2,650 LOC (the audit's split is unstarted)

QKG_AUDIT §4 prescribed splitting `chat.py` into `tools/search.py`, `tools/etymology.py`, `tools/code19.py`, `dispatch.py`, `cache.py`. As of HEAD that has not happened. Today's structure (line ranges from `grep -nE "^# ─"`):

| Lines | Section | LOC | Suggested target |
|---:|---|---:|---|
| 1-26 | imports | 26 | (stays in `chat/__init__.py`) |
| 27-51 | env loading | 25 | `quran_kg.env` (item §1a) |
| 52-109 | semantic model singleton + lemmatizer | 58 | `model_registry` (already exists) |
| 110-156 | input validation helpers | 47 | `tools/_validate.py` |
| 157-712 | 8 graph search/retrieval tools | 556 | `tools/search.py` |
| 714-1132 | 6 etymology tools | 419 | `tools/etymology.py` |
| 1133-1774 | classify_query (English rubric, ~150-line if/elif tree) | 642 | `tools/_classifier.py` (and per retrofit Phase 7 #29: promote to code) |
| 1775-2362 | TOOLS = [...] (Anthropic schema for 21 tools) | 588 | `tools/schema.py` |
| 2363-2592 | tool-result cache + dispatch_tool | 230 | `tools/_cache.py` + `tools/dispatch.py` |
| 2593-2650 | __main__ test loop | 58 | (delete; superseded by tests/) |

**This is the single biggest single-file refactor in the repo.** The body is not duplicated within itself — each tool is genuinely distinct — but the file is too large to navigate without `Ctrl-F`. The audit estimates a one-day split. The split is also a prerequisite for QKG_AUDIT's "consolidate 21 tools toward 8-10" (Phase 7 #28) — easier to merge etymology tools when they live in their own module.

---

## 6 · Lower-priority duplication (worth noting, not urgent)

- **`stdout.reconfigure` Windows shim** in 31 files — purely cosmetic to consolidate.
- **`sys.path.insert(0, str(Path(__file__).parent))`** in 7 files — replace by making the project a real package (`pyproject.toml` already exists; add a `[tool.setuptools]` section or move to `src/` layout). Lower priority than the others.
- **Three `cosine` helpers** (§1c) — when a shared math module emerges, fold them in.
- **Build pipeline scripts** (§2d) sharing the driver-init shape — addressed by the §2a fix.

---

## 7 · What the existing `scripts/` helpers already solve (cross-reference)

The prompt asked to check whether existing helpers in `scripts/` already cover some of this. Findings:

- `scripts/bootstrap_worktree.ps1` is operational (PowerShell only — fresh-worktree hydration) and does not overlap with the Python-side duplications above.
- `scripts/tick_finalize.py` orchestrates state_snapshot + vault_update + MORNING_REPORT — this is Ralph-loop infrastructure (parked, see Pass 1 §2).
- `scripts/state_snapshot.py` knows how to read git log + ralph_state, but is loop-scoped, not a general-purpose helper.
- `scripts/eval_v2.py` is a thin CLI that wraps `eval/v2/runner.py` — good pattern.
- **None of the existing `scripts/` helpers solve the Neo4j driver init / env loader / cache-pass shape duplications flagged above.** Those need a new `quran_kg/` package (or extension to `config.py`).

---

## Aggregate impact

| Refactor | Files touched | LOC removed | Risk |
|---|---:|---:|---|
| §1a `_load_env` → shared helper | 5 | ~60 | Low — pure function |
| §1b `_BRACKET_REF` → call `ref_resolver` | 3-4 | ~30, prevents drift | Low — semantics already aligned |
| §1d `stdout.reconfigure` consolidation | 31 | ~125 | Low — cosmetic |
| §2a Neo4j driver helper | 44 | ~400 | Low — local-only init |
| §2b App-variant FastAPI extraction | 4 | ~400-500 | Medium — needs e2e test per variant |
| §2c `cache_passes` CLI consolidation | 6 | ~150 (after factoring) | Low — pure mechanics |
| §3 Reranker entry-point unification | 3 | ~20, prevents 2nd CrossEncoder load | Low |
| §4 Env-var registry | new file + tests | net +50 | Low |
| §5 `chat.py` split | 1 → ~10 files | 0 (rearrangement) | **High** — touches every dispatch path; needs Phase 3a-style baseline trajectory |
| **Total addressable** | — | **~1,200-1,300 LOC removed** | — |

§5 (chat.py split) is the biggest win cognitively but also the biggest risk — should be its own focused session, not bundled. §2a (Neo4j driver helper) is the highest LOC-removed-per-risk ratio and a great quick win.

---

## Open questions for the operator

1. **App-variant fate.** Phase 3a left the 4 apps as thin wrappers but kept all four. Today's effective production app is `app_free.py`. Are `app.py` / `app_full.py` / `app_lite.py` still wanted as runnable variants, or should they collapse into `app_free.py` with `--profile {paid,full,lite,free}` flags? The audit's "the four-apps duplication is the single biggest tech-debt item" still applies to the **interface layer**, even though Phase 3a fixed the **loop layer**.
2. **Env-var rigor.** Worth landing a Pydantic `Settings` model + a `test_env_keys_documented.py` check, or is the freeform `CLAUDE.md` list "good enough" given the team size?
3. **chat.py split timing.** Should this happen before or after the Phase 7 #28 tool consolidation (21 → 8-10 tools)? Splitting first makes the consolidation easier; consolidating first reduces what gets split. My read: split first.
