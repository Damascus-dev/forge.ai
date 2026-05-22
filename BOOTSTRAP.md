# reccon.ai — Forge Bootstrap

## Identity
AI experimentation sandbox. Local-first, Docker-native, deterministic replay.
5 opencode subagents globally installed (`@sandbox`, `@chaos`, `@replay`, `@observe`, `@tools`).
1 orchestrator subagent (`@orchestrator`) that coordinates sessions and maintains logs.

Between Sprint 2 (Chaos) and Sprint 3 (Observability) in original plan.

## Quick Start
```bash
# API only (no Docker):
cd forge && source .venv/bin/activate && python run.py

# Full Docker stack:
cd forge && docker compose -f docker/docker-compose.yml up -d

# Convenience wrapper:
cd forge && ./forge.sh {start|stop|status|docker-up|docker-down|logs|test}
```

## Endpoints
| URL | Port | Service |
|---|---|---|
| http://localhost:8000 | 8000 | Forge API |
| http://localhost:8000/docs | 8000 | Swagger docs |
| http://localhost:8080/containers/ | 8080 | cAdvisor monitoring UI |

## Repo Map
```
reccon.ai/
├── BOOTSTRAP.md                   ← ENTRY POINT — read this first
├── ai_*_plan.md                   ↑ Original implementation plans
├── forge/                         ↓ Main application
│   ├── api/                       FastAPI routes (experiments, nodes, events, replay)
│   ├── orchestrator/              Experiment lifecycle manager (singleton)
│   ├── agents/loop.py             Agent runtime — STUB (no LLM)
│   ├── chaos/engine.py            Fault injection — STUB (no tc/netem)
│   ├── replay/engine.py           Deterministic replay — WORKING
│   ├── runtime/node.py            Docker node spawning — STUB
│   ├── docker/                    Dockerfile + docker-compose.yml (7 services)
│   ├── forge.sh                   Shell convenience wrapper
│   ├── session_close.sh           Run at session end to finalize logs
│   ├── logs/
│   │   ├── session-summary.md     Latest session summary (auto-generated)
│   │   └── sessions.jsonl         Raw log archive (all agent actions)
│   └── SESSION_HANDOFF.md         Full detailed session handoff

~/.config/opencode/agents/         Global opencode subagents
├── orchestrator.md                Coordinates sessions, runs session_close.sh
├── sandbox.md                     Experiment lifecycle
├── chaos.md                       Fault injection
├── replay.md                      Timeline replay
├── observe.md                     Read-only monitoring
└── tools.md                       Remote node execution
```

## API Surface
| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/health` | Liveness check |
| GET | `/api/v1/experiments/` | List experiments |
| POST | `/api/v1/experiments/` | Create experiment |
| GET | `/api/v1/experiments/{id}` | Get experiment |
| POST | `/api/v1/experiments/{id}/start` | Launch nodes |
| POST | `/api/v1/experiments/{id}/terminate` | Teardown nodes |
| GET | `/api/v1/nodes/{id}` | List nodes |
| POST | `/api/v1/nodes/{id}/inject` | Inject fault |
| GET | `/api/v1/events/{id}` | Get events |
| GET | `/api/v1/replay/{id}/timeline` | Fetch timeline |
| POST | `/api/v1/replay/{id}/start` | Start replay |

## Current State — Real vs Stubs
| Component | Status |
|---|---|
| API endpoints | All defined, working |
| Experiment CRUD | Working (in-memory) |
| Docker compose (7 containers) | Running |
| cAdvisor monitoring | Running on :8080 |
| Subagents (6) | Installed globally |
| Replay engine | Working |
| Chaos engine | **Stubs** — no real tc/netem |
| Docker SDK | **Stubs** — no real container spawn |
| Agent loop | **Stubs** — no LLM integration |
| Redis Streams | **Not wired** (in-memory events) |
| Prometheus/Grafana | Config exists, not in compose |
| Frontend | **Not started** |

## Key Constraints
| Constraint | Detail |
|---|---|
| RAM | 8GB — default node_count=2, avoid heavy inference |
| Docker | Required for full stack; API works standalone too |
| Redis | System Redis on :6379 (Docker Redis is internal-only) |
| Python | 3.12, venv at forge/.venv/ |
| Subagents | Call API via curl — no MCP server |
| Logging | All agents log to /tmp/forge-agent-log.jsonl |
| Session close | Run forge/session_close.sh at end of each session |

## Session History
| When | What |
|---|---|
| Latest | <a href="forge/logs/session-summary.md">2026-05-22T23:54:03Z</a>
| Full handoff | `forge/SESSION_HANDOFF.md` |
| Raw archive | `forge/logs/sessions.jsonl` |

## Next P0 Tasks
1. **Wire real Docker SDK** — replace NodeRuntime stubs with actual docker-py calls
2. **Wire Redis Streams** — replace in-memory event list with Redis Streams
3. **Wire real chaos** — tc/netem via docker exec for real latency/packet loss
4. **Add Prometheus + Grafana** — add to compose, wire cAdvisor metrics to existing dashboard

## Debugging
- API logs: `docker logs docker-api-1` or `./forge.sh logs`
- Agent action logs: `/tmp/forge-agent-log.jsonl`
- Latest session: `forge/logs/session-summary.md`
- Full session handoff: `forge/SESSION_HANDOFF.md`
