import time
from collections import defaultdict

from fastapi import HTTPException, Request
from starlette.middleware.base import BaseHTTPMiddleware

from forge.configs.settings import settings


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Simple in-memory sliding-window rate limiter.

    100 requests per minute per client IP by default.
    Disabled in debug mode.
    """

    def __init__(self, app, max_requests: int = 100, window_seconds: int = 60):
        super().__init__(app)
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: dict[str, list[float]] = defaultdict(list)

    async def dispatch(self, request: Request, call_next):
        if settings.debug:
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        now = time.time()
        window = self.requests[client_ip]

        while window and window[0] < now - self.window_seconds:
            window.pop(0)

        if len(window) >= self.max_requests:
            raise HTTPException(status_code=429, detail="Rate limit exceeded. Try again later.")

        window.append(now)
        return await call_next(request)
