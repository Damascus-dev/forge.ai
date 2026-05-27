# Changelog

## v1.0.0 (2026-05-27)

29 commits across 11 phases delivering a complete distributed system experimentation platform.

### Phase 1-5: MVP Foundation
- Docker Compose sandbox with node spawning and health checks
- Chaos engine: latency, packet_loss, crash, disconnect injection
- Prometheus + Grafana observability stack
- Agent runtime with LiteLLM (observe → reason → act → log)
- Deterministic replay engine with event timeline serialization

### Phase 6: Semantic Logging
- PostgreSQL + pgvector for vector embeddings
- Ollama-powered embedding engine (nomic-embed-text, 768-dim)
- Semantic search API with cosine similarity (<10ms queries)
- Weekly summary generator (APScheduler, auto-generated recaps)
- 48 integration tests, 61 total

### Phase 7: React Flow Visualization
- Custom node types: Experiment, Sandbox, Agent, Event
- Layout algorithms: hierarchical, force-directed, circular
- Chaos visualization with animated indicators
- Agent state panel (observe → reason → act lifecycle)
- Timeline scrubber with event density histogram
- Packet flow animation on network edges
- Replay engine with playback controls (0.25x–4x speed)

### Phase 7.2: Performance & Real-Time
- Layout benchmark: 200 nodes in ~24ms (target <200ms)
- Event clustering for noise reduction
- WebSocket real-time event streaming with auto-reconnect
- Chaos parameter labels on edges (e.g. `latency (delay_ms=200)`)
- PNG screenshot, print-to-PDF, JSON export

### Phase 8: Backend Enhancements
- Enhanced event model (severity, metadata, tags)
- 6 new API endpoints: PATCH/DELETE experiment, metrics, stats, export, health
- Full OpenAPI/Swagger documentation on all 22 endpoints

### Phase 9: Integration & Polish
- 14 E2E API tests covering full experiment lifecycle
- Playwright frontend E2E setup
- Lifespan pattern (replaces deprecated `on_event`)
- Default InMemoryEventStore for stability

### Phase 10: Launch Preparation
- README.md with architecture diagram, quick start, API table
- SECURITY.md with hardening notes
- Security audit: zero hardcoded secrets

### Metrics
- **Commits:** 29
- **Tests:** 91 passing (0 regressions)
- **API endpoints:** 22
- **Frontend:** Next.js 14, React Flow, Framer Motion, Zustand
- **Backend:** FastAPI, Redis, PostgreSQL + pgvector, Docker
