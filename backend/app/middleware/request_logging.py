"""Middleware de logging des requêtes HTTP.

Log chaque requête avec :
- Méthode, path, status code
- Latence
- Request ID unique
- User-Agent
- IP client
"""

from __future__ import annotations

import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from ..config.logging_config import get_logger, request_context_filter

logger = get_logger("middleware.request")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log toutes les requêtes HTTP entrantes et sortantes."""

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4())[:8])
        start_time = time.perf_counter()

        # Injecter le contexte dans les logs
        request_context_filter.set_context(
            request_id=request_id,
            trace_id=request.headers.get("X-Cloud-Trace-Context"),
        )

        # Stocker le request_id pour l'utiliser dans les routes
        request.state.request_id = request_id

        logger.info(
            "%s %s",
            request.method,
            request.url.path,
            extra={
                "extra_data": {
                    "request_id": request_id,
                    "method": request.method,
                    "path": str(request.url.path),
                    "query": str(request.url.query),
                    "client_ip": request.client.host if request.client else "unknown",
                    "user_agent": request.headers.get("user-agent", "unknown"),
                }
            },
        )

        try:
            response = await call_next(request)
            elapsed_ms = (time.perf_counter() - start_time) * 1000

            log_func = logger.info if response.status_code < 400 else logger.warning
            if response.status_code >= 500:
                log_func = logger.error

            log_func(
                "%s %s -> %d (%.0fms)",
                request.method,
                request.url.path,
                response.status_code,
                elapsed_ms,
                extra={
                    "extra_data": {
                        "request_id": request_id,
                        "method": request.method,
                        "path": str(request.url.path),
                        "status_code": response.status_code,
                        "latency_ms": round(elapsed_ms, 2),
                    }
                },
            )

            response.headers["X-Request-ID"] = request_id
            response.headers["X-Response-Time"] = f"{elapsed_ms:.0f}ms"
            return response

        except Exception as exc:
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            logger.critical(
                "Exception non gérée sur %s %s après %.0fms: %s",
                request.method,
                request.url.path,
                elapsed_ms,
                exc,
                exc_info=True,
                extra={
                    "extra_data": {
                        "request_id": request_id,
                        "method": request.method,
                        "path": str(request.url.path),
                        "latency_ms": round(elapsed_ms, 2),
                        "error_type": type(exc).__name__,
                    }
                },
            )
            raise
        finally:
            request_context_filter.clear_context()
