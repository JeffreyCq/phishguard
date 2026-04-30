"""API key generation, verification, and in-memory rate limiting."""
import hashlib
import os
import secrets
from datetime import date, datetime
from typing import Optional

from fastapi import HTTPException
from sqlalchemy import select, update

from database import AsyncSessionLocal
from models import ApiKey

# {prefix: {"count": int, "date": date}}
_rate_counters: dict[str, dict] = {}


def _hash_key(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()


def generate_key() -> tuple[str, str, str]:
    """Return (raw_key, prefix, key_hash). Show raw_key to user once only."""
    token = secrets.token_hex(16)
    raw = f"mdef_{token}"
    prefix = token[:8]
    return raw, prefix, _hash_key(raw)


async def verify_key(raw: Optional[str]) -> ApiKey:
    """Validate key exists, is active, and under rate limit. Raises HTTPException on failure."""
    if not raw:
        raise HTTPException(401, "Missing X-API-Key header.")

    key_hash = _hash_key(raw)

    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(ApiKey).where(ApiKey.key_hash == key_hash)
        )
        api_key = result.scalar_one_or_none()

        if api_key is None or not api_key.is_active:
            raise HTTPException(401, "Invalid or revoked API key.")

        _check_rate_limit(api_key.prefix, api_key.rate_limit)

        await session.execute(
            update(ApiKey)
            .where(ApiKey.prefix == api_key.prefix)
            .values(last_used_at=datetime.utcnow())
        )
        await session.commit()

    return api_key


def _check_rate_limit(prefix: str, limit: int) -> None:
    today = date.today()
    entry = _rate_counters.get(prefix)

    if entry is None or entry["date"] != today:
        _rate_counters[prefix] = {"count": 1, "date": today}
        return

    entry["count"] += 1
    if entry["count"] > limit:
        raise HTTPException(429, f"Rate limit exceeded. Limit: {limit} requests/day.")


def require_admin(x_admin_secret: Optional[str]) -> None:
    secret = os.getenv("ADMIN_SECRET", "")
    if not secret:
        raise HTTPException(503, "Admin API not enabled. Set ADMIN_SECRET env var.")
    if x_admin_secret != secret:
        raise HTTPException(401, "Invalid or missing X-Admin-Secret header.")
