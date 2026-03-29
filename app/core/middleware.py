from __future__ import annotations

import time
import uuid
from collections import defaultdict, deque

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware


class TraceIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        trace_id = request.headers.get("X-Trace-Id", uuid.uuid4().hex)
        request.state.trace_id = trace_id
        response = await call_next(request)
        response.headers["X-Trace-Id"] = trace_id
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    _requests: dict[str, deque[float]] = defaultdict(deque)

    def __init__(self, app, requests_per_minute: int) -> None:
        super().__init__(app)
        self.requests_per_minute = requests_per_minute

    async def dispatch(self, request: Request, call_next):
        client_host = request.client.host if request.client else "unknown"
        now = time.time()
        bucket = self._requests[client_host]
        while bucket and now - bucket[0] > 60:
            bucket.popleft()
        if len(bucket) >= self.requests_per_minute:
            trace_id = getattr(request.state, "trace_id", None)
            return JSONResponse(
                status_code=429,
                content={
                    "error": {
                        "code": "ERR_RATE_LIMIT",
                        "message": "Too many requests",
                        "details": {
                            "limit_per_minute": self.requests_per_minute,
                        },
                        "trace_id": trace_id,
                    }
                },
            )
        bucket.append(now)
        return await call_next(request)

