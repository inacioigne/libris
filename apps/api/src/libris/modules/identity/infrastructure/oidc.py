import asyncio
import json
import logging
import math
import time
from collections.abc import Callable, Mapping
from urllib.parse import urlsplit

import httpx
import jwt

from libris.core.config import Settings
from libris.modules.identity.domain.exceptions import AuthenticationError, ProviderUnavailable

logger = logging.getLogger(__name__)


class OIDCValidator:
    """Application-scoped discovery and bounded JWKS refresh; no token-directed URLs."""

    def __init__(
        self,
        settings: Settings,
        client: httpx.AsyncClient,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self.settings = settings
        self.client = client
        self.clock = clock
        self._keys: list[dict[str, object]] = []
        self._expires = 0.0
        self._retry_after = 0.0
        self._jwks_uri: str | None = None
        self._lock = asyncio.Lock()

    async def _document(self, url: str) -> dict[str, object]:
        try:
            # Bounded provider documents, including when Content-Length is absent.
            async with self.client.stream(
                "GET",
                url,
                timeout=self.settings.oidc_http_timeout_seconds,
                follow_redirects=False,
            ) as response:
                response.raise_for_status()
                body = bytearray()
                async for chunk in response.aiter_bytes():
                    body.extend(chunk)
                    if len(body) > 1_048_576:
                        raise ValueError("Provider document too large")

            value: object = json.loads(body)
            if not isinstance(value, dict):
                raise ValueError("Invalid provider document")
            return value
        except (httpx.HTTPError, ValueError) as exc:
            logger.warning("OIDC provider document unavailable")
            raise ProviderUnavailable() from exc

    async def _refresh(self) -> None:
        now = self.clock()
        if now < self._retry_after:
            raise AuthenticationError()
        self._retry_after = now + self.settings.oidc_jwks_refresh_interval
        if self._jwks_uri is None:
            discovery = await self._document(
                self.settings.oidc_issuer_url.rstrip("/") + "/.well-known/openid-configuration"
            )
            uri = discovery.get("jwks_uri")
            if discovery.get("issuer") != self.settings.oidc_issuer_url or not isinstance(uri, str):
                logger.warning("OIDC discovery configuration rejected")
                raise ProviderUnavailable()
            parts = urlsplit(uri)
            if (
                parts.scheme not in {"http", "https"}
                or not parts.netloc
                or parts.username
                or parts.password
                or parts.fragment
                or (self.settings.app_env == "production" and parts.scheme != "https")
            ):
                raise ProviderUnavailable()
            self._jwks_uri = uri
        document = await self._document(self._jwks_uri)
        keys = document.get("keys")
        if (
            not isinstance(keys, list)
            or not keys
            or len(keys) > 100
            or not all(isinstance(key, dict) for key in keys)
        ):
            logger.warning("OIDC JWKS document rejected")
            raise ProviderUnavailable()
        self._keys = keys
        self._expires = self.clock() + self.settings.oidc_jwks_cache_ttl

    def _matching_key(self, kid: str, algorithm: str) -> jwt.PyJWK | None:
        matches = [
            key
            for key in self._keys
            if key.get("kid") == kid
            and key.get("use", "sig") == "sig"
            and key.get("alg", algorithm) == algorithm
            and (
                "key_ops" not in key
                or (isinstance(key["key_ops"], list) and "verify" in key["key_ops"])
            )
        ]
        if len(matches) != 1:
            return None
        try:
            key = jwt.PyJWK.from_dict(matches[0], algorithm=algorithm)
            if key.key_type not in {"RSA", "EC", "OKP"}:
                return None
            return key
        except (jwt.PyJWTError, ValueError, TypeError, NotImplementedError):
            return None

    async def _key(self, kid: str, algorithm: str) -> jwt.PyJWK:
        async with self._lock:
            key = self._matching_key(kid, algorithm)
            if self.clock() >= self._expires or key is None:
                await self._refresh()
                key = self._matching_key(kid, algorithm)
            if key is None:
                raise AuthenticationError()
            return key

    async def validate(self, token: str) -> Mapping[str, object]:
        if not self.settings.oidc_enabled or len(token) > 16_384:
            raise AuthenticationError()
        try:
            header = jwt.get_unverified_header(token)
            algorithm, kid = header.get("alg"), header.get("kid")
            if (
                algorithm not in self.settings.allowed_oidc_algorithms
                or not isinstance(kid, str)
                or not kid
                or header.get("crit")
            ):
                raise AuthenticationError()
            key = await self._key(kid, algorithm)
            claims: dict[str, object] = jwt.decode(
                token,
                key,
                algorithms=self.settings.allowed_oidc_algorithms,
                issuer=self.settings.oidc_issuer_url,
                audience=self.settings.oidc_audience,
                leeway=self.settings.oidc_clock_skew_seconds,
                options={"require": ["iss", "aud", "exp", "sub"]},
            )
            for name in ("exp", "nbf", "iat"):
                if name in claims:
                    value = claims[name]
                    if (
                        isinstance(value, bool)
                        or not isinstance(value, (int, float))
                        or not math.isfinite(value)
                    ):
                        raise AuthenticationError()
            if claims.get("iss") != self.settings.oidc_issuer_url:
                raise AuthenticationError()
            subject = claims.get("sub")
            if not isinstance(subject, str) or not subject.strip():
                raise AuthenticationError()
            # Keycloak signs typ=Bearer for access tokens and typ=ID for ID tokens.
            # Other providers must configure an equivalent trusted signed claim.
            if (
                claims.get(self.settings.oidc_access_token_claim)
                != self.settings.oidc_access_token_value
            ):
                raise AuthenticationError()
            return claims
        except (jwt.PyJWTError, ValueError, TypeError, OverflowError) as exc:
            logger.debug("OIDC token rejected")
            raise AuthenticationError() from exc
