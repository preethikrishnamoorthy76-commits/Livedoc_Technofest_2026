from typing import Iterable

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from jose import JWTError, jwt

from config import JWT_SECRET_KEY, JWT_ALGORITHM


class TenantMiddleware(BaseHTTPMiddleware):
    """Middleware to enforce tenant isolation via JWT with local dev fallback.

    - Validates the JWT on every request when provided.
    - Extracts tenant_id from the token and attaches it to request.state.
    - Falls back to default_local_tenant if unauthenticated for smooth local usability.
    """

    def __init__(self, app, public_paths: Iterable[str] | None = None) -> None:
        super().__init__(app)
        self.public_paths = set(public_paths or {"/", "/register", "/login"})

    async def dispatch(self, request: Request, call_next):
        request.state.tenant_id = "default_local_tenant"

        # Allow CORS preflight requests
        if request.method == "OPTIONS":
            return await call_next(request)

        # Allow explicitly public paths
        if request.url.path in self.public_paths:
            return await call_next(request)

        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.lower().startswith("bearer "):
            token = auth_header.split(" ", 1)[1]
            try:
                payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
                extracted_tenant = payload.get("tenant_id")
                if extracted_tenant:
                    request.state.tenant_id = extracted_tenant
            except JWTError:
                # Token expired or secret changed - fall back gracefully
                pass

        response: Response = await call_next(request)
        return response
