---
type: decision
adr: 0006
status: accepted
date: 2026-05-10
tags: [decision, infrastructure, hosting]
supersedes: none
---

# ADR-0006 — Stay on local Neo4j Desktop

## Status
Accepted (2026-05-10). Active.

## Context
Three hosting paths were evaluated for Neo4j: (1) local Neo4j Desktop (current), (2) Neo4j Aura free/pro tier (managed cloud), (3) self-hosted VPS. `SESSION_LOG.md` (2026-05-10 session) documents the decision under "Open questions / decisions made." Aura Pro is ~$129/month. Aura free has memory and storage caps that would not accommodate the full 6,234-verse graph with multiple 1024-dim embedding indexes. The project is a solo-developer research tool with infrequent unattended overnight runs.

## Decision
Stay on local Neo4j Desktop. The graph lives at `bolt://localhost:7687`, database `quran`. This is the only officially supported path in the `.env` setup.

## Consequences
- **Positive:** Zero cost. Full control over Neo4j version, memory tuning, and plugin installation. No latency overhead vs. a remote Bolt connection. All data stays local.
- **Negative:** Requires the host PC to be powered on and Neo4j running for any agent tick or UI session. Unattended overnight cron runs depend on the user not shutting down. Not viable for multi-user or production deployment.
- **Neutral:** A VPS migration (e.g., dedicated VM with Neo4j + Python) remains viable if the project outgrows solo-dev use; that path would require a `NEO4J_URI` change only, no schema changes.

## Cross-references
- Source evidence: `repo://SESSION_LOG.md` (2026-05-10 session, "Open questions / decisions made")
- Related: [[0005-skip-aura-agent]]
