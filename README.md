# Forge AI

Distributed system experimentation platform for chaos engineering, AI agent orchestration, and experiment observability.

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                    Frontend (Next.js 14)              │
│  React Flow · Zustand · Framer Motion · Tailwind     │
└──────────────────┬──────────────────────────────────┘
                   │ HTTP / WebSocket
┌──────────────────▼──────────────────────────────────┐
│                    API (FastAPI)                      │
│  Experiments · Nodes · Events · Agents · Replay      │
│  Semantic Search · WebSocket Live Updates            │
└───────┬──────────────────────┬──────────────────────┘
        │                      │
┌───────▼──────┐    ┌─────────▼──────────┐
│  PostgreSQL   │    │  Redis  │  Docker   │
│  + pgvector   │    │ Streams │  Runtime  │
│  (semantic)   │    │ Events  │  Sandbox  │
└───────────────┘    └─────────┴──────────┘
```

## Quick Start

```bash
# Backend
cd forge
python -m venv .venv && source .venv/bin/activate
pip install -e .[dev]
uvicorn forge.api.main:app --reload --port 8000

# Frontend
cd forge/frontend
npm install
npm run dev
```

Open http://localhost:3000

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST   | `/api/v1/experiments/` | Create experiment |
| GET    | `/api/v1/experiments/` | List experiments |
| GET    | `/api/v1/experiments/{id}` | Get experiment |
| PATCH  | `/api/v1/experiments/{id}` | Update experiment |
| DELETE | `/api/v1/experiments/{id}` | Delete experiment |
| POST   | `/api/v1/experiments/{id}/start` | Start experiment |
| POST   | `/api/v1/experiments/{id}/terminate` | Terminate experiment |
| GET    | `/api/v1/experiments/{id}/metrics` | Experiment metrics |
| GET    | `/api/v1/experiments/{id}/events/stats` | Event statistics |
| GET    | `/api/v1/experiments/{id}/export` | Export experiment |
| POST   | `/api/v1/experiments/{id}/agent/start` | Start agent |
| POST   | `/api/v1/experiments/{id}/agent/{aid}/step` | Run agent step |
| GET    | `/api/v1/experiments/{id}/agent/{aid}/logs` | Agent logs |
| GET    | `/api/v1/events/{experiment_id}` | Get events |
| GET    | `/api/v1/nodes/{experiment_id}` | List nodes |
| POST   | `/api/v1/nodes/{experiment_id}/inject` | Inject fault |
| POST   | `/api/v1/replay/{id}/start` | Start replay |
| GET    | `/api/v1/replay/{id}/timeline` | Get timeline |
| GET    | `/health` | Health check |
| GET    | `/metrics` | Prometheus metrics |
| WS     | `/api/v1/experiments/{id}/ws` | Real-time event stream |

Full docs at http://localhost:8000/docs

## Tests

```bash
# Backend (91 tests)
cd forge && source .venv/bin/activate && python -m pytest tests/ -v

# Frontend E2E (requires dev server)
cd forge/frontend && npm run test:e2e
```

## Visualization

The frontend uses React Flow to render experiment topologies with:
- Hierarchical / force-directed / circular layout algorithms
- Real-time agent state (observe → reason → act)
- Animated chaos fault indicators
- Packet flow animation on network edges
- Replay timeline scrubber with playback controls
- Event density histogram
- PNG/PDF export

## Phases

| Phase | Status | Description |
|-------|--------|-------------|
| 1-5   | ✅ | MVP foundation (runtime, chaos, observability, agents, replay) |
| 6     | ✅ | Semantic logging (PostgreSQL + pgvector + Ollama embeddings) |
| 7     | ✅ | React Flow visualization, timeline, replay, packet animation |
| 7.2   | ✅ | Performance, real-time WebSocket, event clustering, export |
| 8     | ✅ | Backend enhancements (6 new endpoints, enhanced models, Swagger) |
| 9     | ✅ | E2E tests, Playwright, performance optimization |
| 10    | 🔄 | Launch preparation (docs, GitHub, security audit) |
| 11    | ⏳ | Public launch |
