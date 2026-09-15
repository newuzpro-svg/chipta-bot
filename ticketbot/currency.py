import logging
import time

import httpx

logger = logging.getLogger(__name__)

_CACHE_TTL_SECONDS = 6 * 60 * 60
_FALLBACK_RUB_RATE = 140.0  # used only if O'zbekiston Markaziy Banki API is unreachable

_cached_rate: float | None = None
_cached_at: float = 0.0


async def get_rub_to_uzs_rate() -> float:
    global _cached_rate, _cached_at
    if _cached_rate is not None and time.time() - _cached_at < _CACHE_TTL_SECONDS:
        return _cached_rate
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get("https://cbu.uz/uz/arkhiv-kursov-valyut/json/RUB/")
            resp.raise_for_status()
            data = resp.json()
            rate = float(data[0]["Rate"])
        _cached_rate = rate
        _cached_at = time.time()
        return rate
    except Exception as exc:
        logger.warning("CBU RUB rate olinmadi, taxminiy kursdan foydalanaman: %s", exc)
        return _cached_rate or _FALLBACK_RUB_RATE


async def rub_to_uzs(amount_rub: float) -> int:
    rate = await get_rub_to_uzs_rate()
    return round(amount_rub * rate)
