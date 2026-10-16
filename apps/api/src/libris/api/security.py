"""Response controls outside ServerErrorMiddleware, including CORS preflight/500."""

import re

from starlette.datastructures import Headers
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import PlainTextResponse
from starlette.types import ASGIApp, Message, Receive, Scope, Send


class EndpointCORSMiddleware(CORSMiddleware):
    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if (
            scope["type"] == "http"
            and scope["method"] == "OPTIONS"
            and b"access-control-request-method" in dict(scope.get("headers", []))
        ):
            path = scope["path"]
            allowed = {"GET"} if path in {"/health", "/api/v1/identity/me"} else set()
            if re.fullmatch(r"/api/v1/catalog/(works|instances|items|agents|subjects)", path):
                allowed = {"POST"}
            elif re.fullmatch(
                r"/api/v1/catalog/(works|instances|items|agents|subjects)/"
                r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-"
                r"[0-9a-fA-F]{4}-[0-9a-fA-F]{12}",
                path,
            ):
                allowed = {"GET", "PATCH"}
            method = dict(scope["headers"])[b"access-control-request-method"].decode("latin-1")
            if not allowed:
                await PlainTextResponse("CORS endpoint rejected", status_code=400)(
                    scope, receive, send
                )
                return
            response = self.preflight_response(Headers(scope=scope))
            response.headers["Access-Control-Allow-Methods"] = ", ".join(sorted(allowed))
            if method not in allowed:
                response = PlainTextResponse(
                    "CORS method rejected",
                    status_code=400,
                    headers={
                        key: value
                        for key, value in response.headers.items()
                        if key.lower() != "content-length"
                    },
                )
            await response(scope, receive, send)
            return
        await super().__call__(scope, receive, send)


class SecurityHeadersMiddleware:
    def __init__(self, app: ASGIApp, *, production: bool) -> None:
        self.app = app
        self.production = production

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        async def protected_send(message: Message) -> None:
            if message["type"] == "http.response.start":
                policy = {
                    b"x-content-type-options": b"nosniff",
                    b"referrer-policy": b"no-referrer",
                    b"x-frame-options": b"DENY",
                    b"permissions-policy": b"camera=(), microphone=(), geolocation=()",
                    b"content-security-policy": (
                        b"default-src 'none'; frame-ancestors 'none'; base-uri 'none'"
                    ),
                }
                # Interactive docs are development-only and use FastAPI's CDN/inline UI.
                if not self.production and scope["path"] in {"/docs", "/redoc"}:
                    policy[b"content-security-policy"] = (
                        b"default-src 'none'; script-src https://cdn.jsdelivr.net 'unsafe-inline'; "
                        b"style-src https://cdn.jsdelivr.net 'unsafe-inline'; "
                        b"img-src https://fastapi.tiangolo.com data:; connect-src 'self'; "
                        b"frame-ancestors 'none'; base-uri 'none'"
                    )
                if self.production and scope["scheme"] == "https":
                    policy[b"strict-transport-security"] = b"max-age=31536000"
                supplied = scope.get("headers", [])
                if (
                    scope["path"].startswith("/api/")
                    or any(key.lower() in {b"authorization", b"cookie"} for key, _ in supplied)
                    or message["status"] >= 400
                ):
                    policy[b"cache-control"] = b"no-store, private"
                    policy[b"pragma"] = b"no-cache"
                headers = message.get("headers", [])
                message["headers"] = [
                    (key, value)
                    for key, value in headers
                    if key.lower() not in policy and key.lower() != b"server"
                ] + list(policy.items())
            await send(message)

        await self.app(scope, receive, protected_send)
