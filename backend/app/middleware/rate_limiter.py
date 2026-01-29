"""Middleware de rate limiting simple basé sur la mémoire."""

from __future__ import annotations

import time
from collections import defaultdict

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from ..config.logging_config import get_logger
from ..config.settings import get_settings

logger = get_logger("middleware.rate_limiter")


class RateLimiterMiddleware(BaseHTTPMiddleware):
    """Limite le nombre de requêtes par minute par IP."""

    def __init__(self, app, calls_per_minute: int | None = None) -> None:  # type: ignore[no-untyped-def]
        super().__init__(app)
        settings = get_settings()
        self._limit = calls_per_minute or settings.rate_limit_per_minute
        self._window = 60  # secondes
        self._requests: dict[str, list[float]] = defaultdict(list)

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        # Ne limiter que les endpoints API
        if not request.url.path.startswith("/api/"):
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        now = time.time()

        # Nettoyer les anciennes entrées
        self._requests[client_ip] = [
            t for t in self._requests[client_ip] if now - t < self._window
        ]

        if len(self._requests[client_ip]) >= self._limit:
            logger.warning(
                "Rate limit atteint pour %s (%d/%d requêtes)",
                client_ip,
                len(self._requests[client_ip]),
                self._limit,
                extra={
                    "extra_data": {
                        "client_ip": client_ip,
                        "requests_count": len(self._requests[client_ip]),
                        "limit": self._limit,
                    }
                },
            )
            return JSONResponse(
                status_code=429,
                content={
                    "error": "Rate limit exceeded",
                    "detail": f"Maximum {self._limit} requêtes par minute",
                    "retry_after": self._window,
                },
                headers={"Retry-After": str(self._window)},
            )

        self._requests[client_ip].append(now)
        return await call_next(request)
