import asyncio
import logging

import httpx

from ticketbot.config import PROXY_ENABLED
from ticketbot.proxy import pool

logger = logging.getLogger(__name__)

_BLOCKED_STATUSES = {403, 429, 503}


async def request_with_fallback(method: str, url: str, *, headers: dict | None = None,
                                 json: dict | None = None, cookies: dict | None = None,
                                 timeout: float = 20.0) -> httpx.Response:
    """Do the request directly; if the site seems to be blocking us (connection
    error or a 403/429/503), retry once through a free proxy."""
    try:
        async with httpx.AsyncClient(timeout=timeout, cookies=cookies) as client:
            resp = await client.request(method, url, headers=headers, json=json)
        if resp.status_code not in _BLOCKED_STATUSES:
            return resp
        logger.warning("%s returned %s, will try proxy fallback", url, resp.status_code)
    except httpx.RequestError as exc:
        logger.warning("Direct request to %s failed (%s), will try proxy fallback", url, exc)

    if not PROXY_ENABLED:
        raise ConnectionError(f"{url} unreachable and proxy fallback disabled")

    proxy_url = await asyncio.to_thread(pool.get_working_proxy, url)
    if not proxy_url:
        raise ConnectionError(f"{url} unreachable and no working free proxy found")

    async with httpx.AsyncClient(timeout=timeout, cookies=cookies, proxy=proxy_url) as client:
        return await client.request(method, url, headers=headers, json=json)
