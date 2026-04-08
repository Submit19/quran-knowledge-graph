# Quran Knowledge Graph

An interactive AI-powered Quran explorer that connects all 6,234 verses from Rashad Khalifa's translation (*The Final Testament*) through a thematic knowledge graph. Ask questions in natural language and get answers grounded in actual verses, with a 3D visualization showing how they connect.

## What It Does

- **Conversational search** -- Ask anything about the Quran. Claude explores the graph using 6 tools and returns answers citing specific verses `[2:255]` that you can hover over to read the full text.
- **3D graph visualization** -- 6,234 verses arranged on a Fibonacci sphere by surah. Connections light up in real-time as Claude explores. Fly through with WASD controls.
- **Statistical dashboard** -- Interactive presentation of graph topology, keyword frequencies, cross-surah connections.

## Architecture

```
User Question
    |
POST /chat (FastAPI, app.py)
    |
Claude API (agentic tool-use loop, chat.py)
    | calls tools |
Neo4j Graph Database (Cypher + vector index)
    | returns results |
SSE Event Stream --> Frontend (index.html)
    |
- Text deltas stream into chat bubble (markdown via marked.js)
- Tool calls shown as expandable <details> blocks
- graph_update events inject nodes/links into 3D visualization
- On completion, all cited [sura:verse] refs get hoverable tooltips
```

### SSE Event Types

| Event | Purpose |
|-------|---------|
| `text` | Claude's response text, streamed incrementally |
| `tool` | Tool execution (name, args, summary) shown as expandable block |
| `graph_update` | Nodes + links to add to 3D visualization |
| `done` | All referenced verse texts for tooltip rendering |
| `error` | Error message |

### Backend Streaming Pattern

The agentic loop runs in a **daemon thread** pushing events onto a `queue.SimpleQueue()`. The async generator polls the queue with `asyncio.sleep(0.05)`. A `None` sentinel signals completion. This bridges Claude's synchronous streaming API with FastAPI's async SSE response.

## Graph Schema (Neo4j)

### Node Types

| Label | Count | Key Properties | Description |
|-------|-------|----------------|-------------|
| `Verse` | 6,234 | `verseId` ("2:255"), `reference` (alias), `surah`, `verseNum`, `surahName`, `text`, `sura`, `number`, `embedding` (384-dim vector) | Every verse in the Quran (Rashad Khalifa translation). Verses 9:128-129 excluded per this translation. |
| `Keyword` | 2,636 | `keyword` | Lemmatized keywords extracted via TF-IDF. 25 generic stopwords removed during migration. |
| `Sura` | 114 | `number` | Surah container nodes. |
| `GraphMeta` | 1 | `key`, `name`, `note_9_128_129`, `total_verses`, `surahs`, `migration_date` | Translation metadata and schema documentation. |

### Relationship Types

| Type | Count | Direction | Properties | Description |
|------|-------|-----------|------------|-------------|
| `RELATED_TO` | 51,798 | Verse -- Verse | `score` (float, 0.1-3.82) | Thematic similarity via shared rare keywords. Capped at 12 per verse. 93.7% are cross-surah. |
| `MENTIONS` | 41,138 | Verse --> Keyword | `score` (float, 0.04-1.0) | TF-IDF weighted verse-to-keyword association. |
| `CONTAINS` | 6,234 | Sura --> Verse | none | Structural containment. |
| `NEXT_VERSE` | 6,233 | Verse --> Verse | none | Sequential reading order (within + cross-surah). |

### Indexes and Constraints

| Name | Type | Label | Property |
|------|------|-------|----------|
| `verse_id` | UNIQUE | Verse | `verseId` |
| `verse_ref` | UNIQUE | Verse | `reference` |
| `verse_surah` | RANGE | Verse | `surah` |
| `verse_embedding` | VECTOR | Verse | `embedding` |
| `sura_num` | UNIQUE | Sura | `number` |
| `kw_id` | UNIQUE | Keyword | `keyword` |

## Claude's Tools (chat.py)

| Tool | Function | What it queries |
|------|----------|-----------------|
| `search_keyword(keyword)` | Find ALL verses containing a word/phrase in English text | `WHERE toLower(v.english) CONTAINS toLower($keyword)` -- no limit, returns all matches grouped by surah |
| `semantic_search(query, top_k=40)` | Meaning-based search via embeddings | Neo4j vector index on `embedding` property, cosine similarity, returns top_k results |
| `traverse_topic(keywords, depth=2)` | Multi-keyword search + graph traversal | Finds seed verses via keywords, then traverses 1-2 hops via `RELATED_TO` edges |
| `get_verse(ref)` | Deep-dive into one verse | Returns verse text + 12 nearest neighbours via `RELATED_TO` + shared keywords (batched UNWIND query) |
| `find_path(from_ref, to_ref)` | Shortest thematic path between two verses | `shortestPath` via `RELATED_TO` edges + bridge keywords (batched UNWIND query) |
| `explore_surah(surah_number)` | Map a full chapter | All verses in surah + cross-surah `RELATED_TO` connections + top keywords |

### System Prompt

The system prompt (`SYSTEM_PROMPT` in chat.py) instructs Claude to:
- Always search before answering (never rely on general knowledge)
- Cite every claim with inline `[sura:verse]` bracket notation
- Use multiple tools per question (keyword search first, then semantic search, then traversal)
- Deduplicate results across tool calls
- Stay grounded in graph data

### Citation Rules

Every `[sura:verse]` reference in Claude's response becomes a hoverable tooltip in the frontend. After the agentic loop completes, `app.py` extracts all bracket references via regex `\[(\d+:\d+)\]`, batch-fetches their texts from Neo4j, and sends them in the `done` event.

## 3D Visualization (index.html)

### Libraries
- Three.js (r160) -- 3D rendering
- 3d-force-graph (v1) -- force-directed layout
- marked.js (v9) -- markdown rendering

### Galaxy Layout
- All 6,234 verses pre-positioned on a **Fibonacci sphere** (radius 600)
- 114 surah centers distributed via `fibSphere(i, 114, R)`
- Verses within each surah form **perpendicular rings** around the surah center
- Ring radius: `min(20 + n * 0.55, 90)` where n = verse count in surah

### Background Point Cloud
- All verses rendered as a single `THREE.Points` buffer geometry (one draw call)
- Hue spread by surah number, saturation 0.5, lightness 0.18
- Point size 2.2, opacity 0.6

### Conversation Nodes
When `graph_update` events arrive:
- Verse nodes pinned to their pre-computed `GALAXY_POSITIONS[v:id]` (`fx/fy/fz`)
- Keyword nodes pinned to the centroid of their connected verse positions
- Active nodes get bright color + aura glow (larger transparent BackSide sphere)
- Labels rendered as canvas-based Three.js sprites

### Color Scheme (Dark Theme)
- Background: `#060a14`
- Cards/panels: `#0f1a2e`
- Primary accent: `#10b981` (emerald green)
- Secondary accent: `#f59e0b` (gold/keywords)
- Text: `#cbd5e1`
- Borders: `#1e293b`

### Camera Controls
- Orbit: drag
- Zoom: scroll
- WASD fly-through with Q/E for up/down
- Click node: shows info card

## Data Pipeline

### Step 1: Parse PDF (`parse_quran.py`)
Extracts all 6,234 verses from Rashad Khalifa's PDF translation into `data/verses.json`. Handles surah headers, verse numbering, multi-line verses, and footnote markers.

### Step 2: Build Graph (`build_graph.py`)
- TF-IDF vectorization with NLTK WordNet lemmatizer
- Custom stopword list (Quranic + English)
- Produces 2,636 keywords with weighted MENTIONS edges
- Computes pairwise verse similarity via shared rare keywords
- Caps RELATED_TO edges at 12 per verse, minimum score threshold
- Outputs 4 CSV files for Neo4j import

### Step 3: Import (`import_neo4j.py`)
- Batch import of CSV files into Neo4j
- Creates uniqueness constraints and indexes
- `LOAD CSV` for Verse nodes, Keyword nodes, MENTIONS edges, RELATED_TO edges

### Step 4: Embed (`embed_verses.py`)
- `all-MiniLM-L6-v2` sentence-transformer (384-dim)
- Batch encoding (256 at a time)
- Stored as `embedding` property on Verse nodes
- Neo4j vector index created for cosine similarity search

### Step 5: Migrate (`migrate_graph.py`)
Post-build quality improvements:
- Merged dual-schema verse populations into unified schema
- Rebuilt CONTAINS and NEXT_VERSE structural edges
- Connected 33 orphan Muqatta'at verses to neighbours
- Removed 25 generic stopword keywords and 3,926 noisy MENTIONS edges
- Added GraphMeta node documenting the translation choice

## Key Stats (Post-Migration)

| Metric | Value |
|--------|-------|
| Verses | 6,234 across 114 surahs |
| Keywords | 2,636 (stopwords filtered) |
| MENTIONS edges | 41,138 |
| RELATED_TO edges | 51,798 |
| NEXT_VERSE edges | 6,233 |
| CONTAINS edges | 6,234 |
| Cross-surah connections | 93.7% of RELATED_TO edges |
| Avg keywords per verse | ~6.6 |
| Embedding dimensions | 384 (all-MiniLM-L6-v2) |
| Strongest verse pair | 4:43 <-> 5:6 (ablution rules, score 3.82) |

## Known Limitations

1. **Keyword extraction** -- TF-IDF works at the word level. Multi-word concepts ("day of judgment", "children of Israel") are split into individual keywords, losing compound meaning.
2. **Embedding model** -- `all-MiniLM-L6-v2` is a general English model, not fine-tuned on Quranic/religious text. Domain-specific embeddings would improve semantic search.
3. **RELATED_TO cap** -- Each verse has at most 12 RELATED_TO edges. Some highly thematic verses may have relevant connections that were pruned.
4. **No Arabic text** -- The graph contains only the English translation. Arabic original text is not stored.
5. **No cross-reference to traditional tafsir** -- Connections are purely algorithmic (TF-IDF + embeddings), not informed by classical commentary traditions.
6. **No verse-level metadata** -- Missing: revelation order (Meccan/Medinan), occasion of revelation (asbab al-nuzul), abrogation status.
7. **Single translation** -- Rashad Khalifa's translation only. No comparison with other translations (Sahih International, Pickthall, Yusuf Ali, etc.).

## File Structure

```
quran-knowledge-graph/
  parse_quran.py       -- PDF to structured JSON
  build_graph.py       -- TF-IDF keyword extraction + edge computation
  import_neo4j.py      -- Batch import into Neo4j
  embed_verses.py      -- Sentence-transformer embeddings + vector index
  migrate_graph.py     -- Schema unification + quality improvements
  chat.py              -- Claude agent with 6 graph tools + system prompt
  app.py               -- FastAPI web UI with streaming + 3D graph (port 8081)
  server.py            -- OpenAI-compatible REST API
  ui.py                -- Gradio chatbot interface
  explore.py           -- CLI graph exploration tool
  index.html           -- 3D graph visualization (Three.js + ForceGraph3D)
  stats.html           -- Statistical insights dashboard
  make_stats_pptx.js   -- PowerPoint stats generator
  graph_audit_report.md -- Full database audit results
  .env                 -- API keys and database credentials (not committed)
  data/
    verses.json              -- All 6,234 parsed verses
    verse_nodes.csv          -- Verse node data for Neo4j import
    keyword_nodes.csv        -- Keyword node data
    verse_keyword_rels.csv   -- MENTIONS edges with TF-IDF scores
    verse_related_rels.csv   -- RELATED_TO edges with similarity scores
```

## Setup

### Prerequisites
- Python 3.10+
- Neo4j Desktop (Community Edition)
- Anthropic API key

### Install
```bash
pip install neo4j anthropic python-dotenv sentence-transformers scikit-learn nltk fastapi uvicorn
```

### Configure
Create a `.env` file:
```
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password
NEO4J_DATABASE=quran
ANTHROPIC_API_KEY=your_key
```

### Build the Graph
```bash
python parse_quran.py      # PDF -> verses.json
python build_graph.py      # TF-IDF keywords + edges -> CSVs
python import_neo4j.py     # CSVs -> Neo4j
python embed_verses.py     # Sentence-transformer embeddings
python migrate_graph.py    # Schema unification + quality fixes
```

### Run
```bash
python app.py              # Web UI at http://localhost:8081
```

## Tech Stack

- **Graph database**: Neo4j (Cypher queries, vector index, uniqueness constraints)
- **AI**: Claude Sonnet 4.5 via Anthropic API (agentic tool-use with streaming)
- **Embeddings**: sentence-transformers (`all-MiniLM-L6-v2`, 384-dim)
- **NLP**: scikit-learn TF-IDF, NLTK WordNet lemmatization
- **Frontend**: Three.js r160, 3d-force-graph v1, marked.js v9, vanilla JS
- **Backend**: FastAPI + uvicorn, SSE streaming via daemon thread + SimpleQueue
- **Translation**: Rashad Khalifa's *Quran: The Final Testament* (6,234 verses, excludes 9:128-129)

## License

MIT
