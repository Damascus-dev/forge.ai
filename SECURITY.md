# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| v1.0.x  | ✅ Active development |

## Secrets & Credentials

- No secrets or credentials are hardcoded in this repository.
- Environment variables are loaded from `forge/.env` (gitignored).
- The `.env` file contains only non-sensitive defaults (`FORGE_REDIS_URL`, `FORGE_SQLITE_PATH`, `FORGE_DEBUG`).
- Database credentials are configured via environment variables at deployment time.

## Best Practices

- **API**: CORS is open during development (`allow_origins=["*"]`) — restrict in production.
- **Docker**: Containers run with minimal privileges, no volume mounts to sensitive paths.
- **Prometheus**: Metrics endpoint (`/metrics`) is unauthenticated — protect in production.
- **WebSocket**: Real-time event streams are per-experiment — no authentication currently implemented.

## Reporting Issues

Open a GitHub issue for any security concerns.
