"""
Supabase JWT verification.

Modern Supabase projects sign access tokens with ES256 (asymmetric). The
public key is published at the project's JWKS endpoint, so verification is
a local operation after the first JWKS fetch (cached by PyJWKClient).

The legacy HS256 path (verifying with the JWT secret) is kept as a fallback
in case the project is on the older asymmetric-disabled config.
"""
from functools import lru_cache
from typing import Optional

import jwt
from jwt import PyJWKClient

from backend.core.config import get_settings

_settings = get_settings()


@lru_cache(maxsize=1)
def _jwks_client() -> Optional[PyJWKClient]:
    """Return a cached JWKS client for the configured Supabase project."""
    if not _settings.supabase_url:
        return None
    url = _settings.supabase_url.rstrip("/") + "/auth/v1/.well-known/jwks.json"
    # cache_keys=True keeps signing keys in memory; lifespan refreshes the JWKS hourly.
    return PyJWKClient(url, cache_jwk_set=True, lifespan=3600)


def verify_token(token: str) -> Optional[dict]:
    """Verify a Supabase access token; return claims or None on failure."""
    try:
        header = jwt.get_unverified_header(token)
    except jwt.PyJWTError:
        return None

    alg = header.get("alg", "HS256")

    # Asymmetric path (ES256/RS256/EdDSA) — fetch the public key via JWKS.
    if alg in ("ES256", "ES384", "ES512", "RS256", "RS384", "RS512", "EdDSA"):
        client = _jwks_client()
        if client is None:
            return None
        try:
            key = client.get_signing_key_from_jwt(token).key
            return jwt.decode(
                token,
                key,
                algorithms=[alg],
                audience=_settings.supabase_jwt_audience,
            )
        except jwt.PyJWTError:
            return None

    # Legacy symmetric (HS256) path.
    if not _settings.supabase_jwt_secret:
        return None
    try:
        return jwt.decode(
            token,
            _settings.supabase_jwt_secret,
            algorithms=[alg],
            audience=_settings.supabase_jwt_audience,
        )
    except jwt.PyJWTError:
        return None
