# reccon.ai — Forge Bootstrap

## Identity
AI experimentation sandbox. Local-first, Docker-native, deterministic replay.
5 opencode subagents globally installed (`@sandbox`, `@chaos`, `@replay`, `@observe`, `@tools`).
1 orchestrator subagent (`@orchestrator`) that coordinates sessions and maintains logs.

All 5 sprints from the original plan are implemented.

## Quick Start
```bash
# API only (no Docker):
cd forge && source .venv/bin/activate && python run.py

# Full Docker stack (9 services):
cd forge && docker compose -f docker/docker-compose.yml up -d --build

# Frontend standalone:
cd forge/frontend && npm run dev

# Convenience wrapper:
cd forge && ./forge.sh {start|stop|status|docker-up|docker-down|logs|test}
```

## Endpoints
| URL | Port | Service |
|---|---|---|
| http://localhost:8000 | 8000 | Forge API |
| http://localhost:8000/docs | 8000 | Swagger docs |
| http://localhost:8000/metrics | 8000 | Prometheus metrics |
| http://localhost:3000 | 3000 | Grafana (admin/admin) |
| http://localhost:3000 | 3000 | Frontend (standalone) |
| http://localhost:3001 | 3001 | Frontend (Docker stack) |
| http://localhost:9090 | 9090 | Prometheus UI |
| http://localhost:8080/containers/ | 8080 | cAdvisor monitoring UI |

## Repo Map
```
reccon.ai/
├── BOOTSTRAP.md                   ← ENTRY POINT — read this first
├── ai_*_plan.md                   ↑ Original implementation plans
├── forge/                         ↓ Main application
│   ├── api/                       FastAPI routes (experiments, nodes, events, replay, agents, metrics)
│   ├── orchestrator/              Experiment lifecycle manager (singleton)
│   ├── agents/loop.py             Agent runtime — LiteLLM integration
│   ├── chaos/engine.py            Fault injection — real tc/netem via docker exec
│   ├── replay/engine.py           Deterministic replay — WORKING
│   ├── runtime/node.py            Docker node spawning — real docker-py
│   ├── events/store.py            Event store — Redis Streams + in-memory fallback
│   ├── tools/base.py              Agent tools — exec, read_file, restart_service
│   ├── telemetry/metrics.py       Prometheus metrics
│   ├── configs/                   Settings, prometheus config, grafana datasources
│   ├── dashboards/                Grafana dashboard JSON
│   ├── docker/                    Dockerfile + docker-compose.yml (9 services)
│   ├── frontend/                  Next.js 14 dashboard
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
| GET | `/metrics` | Prometheus metrics |
| GET | `/api/v1/experiments/` | List experiments |
| POST | `/api/v1/experiments/` | Create experiment |
| GET | `/api/v1/experiments/{id}` | Get experiment |
| POST | `/api/v1/experiments/{id}/start` | Launch nodes |
| POST | `/api/v1/experiments/{id}/terminate` | Teardown nodes |
| GET | `/api/v1/nodes/{id}` | List nodes |
| POST | `/api/v1/nodes/{id}/inject` | Inject fault (latency, packet_loss, crash, disconnect) |
| GET | `/api/v1/events/{id}` | Get events |
| GET | `/api/v1/replay/{id}/timeline` | Fetch timeline |
| POST | `/api/v1/replay/{id}/start` | Start replay |
| POST | `/api/v1/experiments/{id}/agent/start` | Start AI agent |
| POST | `/api/v1/experiments/{id}/agent/{aid}/step` | Run agent step |
| GET | `/api/v1/experiments/{id}/agent/{aid}/logs` | Get agent logs |

## Current State — Real vs Stubs
| Component | Status |
|---|---|
| API endpoints | All defined, working |
| Experiment CRUD | Working (in-memory) |
| Event store | **Redis Streams** (falls back to in-memory) |
| Docker SDK | **Real docker-py** — spawns/tears down Alpine containers |
| Chaos engine | **Real tc/netem** — latency, packet loss, crash, disconnect |
| Agent loop | **LiteLLM** — calls any OpenAI-compatible model with tool calling |
| Docker compose (9 services) | API, Redis, cAdvisor, Prometheus, Grafana, Frontend, 3x nodes |
| Frontend | **Next.js 14 dashboard** — experiment list, detail, replay, agent control |
| Prometheus/Grafana | **Running** — auto-provisioned with Forge dashboard |
| Replay engine | Working |
| Subagents (6) | Installed globally |

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
| LLM | Agent defaults to `ollama/qwen2.5:7b` — set `model` for OpenAI/Anthropic/etc |

## Session History
| When | What |
|---|---|
| Latest | <a href="forge/logs/session-summary.md">2026-05-23T00:59:16Z</a>
| Full handoff | `forge/SESSION_HANDOFF.md` |
| Raw archive | `forge/logs/sessions.jsonl` |

## Next Tasks
All original sprints complete. Future directions:
1. **Multi-host orchestration** — distribute nodes across machines
2. **Persistent SQLite/Postgres** — replace in-memory experiment storage
3. **Advanced chaos profiles** — CPU/memory pressure, clock skew, bandwidth throttling
4. **Agent teams** — multi-agent collaboration experiments
5. **OSS release** — GitHub, docs, demos

## Debugging
- API logs: `docker logs docker-api-1` or `./forge.sh logs`
- Agent action logs: `/tmp/forge-agent-log.jsonl`
- Latest session: `forge/logs/session-summary.md`
- Full session handoff: `forge/SESSION_HANDOFF.md`
