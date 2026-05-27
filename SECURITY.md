# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| v1.0.x  | ✅ Active development |

## Authentication

- **API Key**: Set `FORGE_API_KEY` in `.env` to enable authentication via the `X-API-Key` header.
- **Debug mode**: When `FORGE_DEBUG=true` (default), authentication is disabled and CORS allows all origins.
- **Production**: Set `FORGE_DEBUG=false` and `FORGE_API_KEY` to a strong random value.
- **WebSocket**: Requires `?api_key=` query parameter when auth is enabled.
- **Metrics**: The `/metrics` endpoint is protected by the same API key.

## CORS

- In debug mode, all origins are allowed (`*`).
- In production, defaults to `http://localhost:3000,http://localhost:3001,http://localhost:8000`.
- Override with `FORGE_ALLOWED_ORIGINS` (comma-separated).

## Event Store

- Default is in-memory (all data lost on restart).
- Set up Redis for persistent event storage.
- A startup warning is logged when Redis is unavailable.

## Secrets & Credentials

- No secrets or credentials are hardcoded in this repository.
- Environment variables are loaded from `forge/.env` (gitignored).
- Database credentials are configured via environment variables at deployment time.

## Best Practices

- **Docker**: Containers run with minimal privileges, no volume mounts to sensitive paths.
- **CI**: Automated test suite runs on every push (pytest, ruff, mypy, eslint).

## Reporting Issues

**For critical vulnerabilities**, report privately via [GitHub Security Advisories](https://github.com/Damascus-dev/forge.ai/security/advisories/new) or email **security@forge.ai** (if configured).

For non-critical issues, open a public GitHub issue.
