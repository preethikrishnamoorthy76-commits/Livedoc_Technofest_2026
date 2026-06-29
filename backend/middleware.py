from typing import Iterable

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from jose import JWTError, jwt

from config import JWT_SECRET_KEY, JWT_ALGORITHM


class TenantMiddleware(BaseHTTPMiddleware):
    """Middleware to enforce tenant isolation via JWT.

    - Validates the JWT on (almost) every request.
    - Extracts tenant_id from the token and attaches it to request.state.
    - Intended to be used together with database queries that always filter by tenant_id.
    """

    def __init__(self, app, public_paths: Iterable[str] | None = None) -> None:
        super().__init__(app)
        # Paths that do not require authentication, e.g. health checks, auth endpoints.
        self.public_paths = set(public_paths or {"/", "/register", "/login"})

    async def dispatch(self, request: Request, call_next):
        request.state.tenant_id = None

        # Let CORS preflight requests pass through so the browser can
        # negotiate allowed methods/headers before sending the real request.
        if request.method == "OPTIONS":
            return await call_next(request)

        # Allow unauthenticated access for explicitly public paths.
        if request.url.path in self.public_paths:
            return await call_next(request)

        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.lower().startswith("bearer "):
            return JSONResponse(
                status_code=401,
                content={"detail": "Authorization header with Bearer token required"},
            )

        token = auth_header.split(" ", 1)[1]
        try:
            payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        except JWTError:
            return JSONResponse(
                status_code=401,
                content={"detail": "Invalid or expired token"},
            )

        tenant_id = payload.get("tenant_id")
        if not tenant_id:
            return JSONResponse(
                status_code=401,
                content={"detail": "Token missing tenant_id"},
            )

        # Attach tenant_id to request context so handlers and DB helpers can enforce filtering.
        request.state.tenant_id = tenant_id

        response: Response = await call_next(request)
        return response
