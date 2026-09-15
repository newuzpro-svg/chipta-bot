import logging
import random
import time

import httpx

logger = logging.getLogger(__name__)

# Public, free proxy-list aggregators. No API key needed. Free proxies are
# unreliable (slow, often dead) so this is only used as a fallback after the
# direct connection starts failing/getting blocked.
_PROXY_SOURCES = [
    "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt",
    "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/http.txt",
    "https://api.proxyscrape.com/v2/?request=getproxies&protocol=http&timeout=5000&country=all&ssl=all&anonymity=all",
]

_REFRESH_INTERVAL_SECONDS = 30 * 60


class ProxyPool:
    def __init__(self) -> None:
        self._proxies: list[str] = []
        self._good: list[str] = []
        self._last_refresh = 0.0

    def _refresh(self) -> None:
        if time.time() - self._last_refresh < _REFRESH_INTERVAL_SECONDS and self._proxies:
            return
        self._last_refresh = time.time()
        collected: list[str] = []
        for url in _PROXY_SOURCES:
            try:
                resp = httpx.get(url, timeout=10)
                resp.raise_for_status()
                for line in resp.text.splitlines():
                    line = line.strip()
                    if line and ":" in line:
                        collected.append(line)
            except Exception as exc:
                logger.warning("Proxy source %s failed: %s", url, exc)
        random.shuffle(collected)
        self._proxies = collected[:200]
        self._good = []
        logger.info("Refreshed proxy pool: %d candidates", len(self._proxies))

    def get_working_proxy(self, test_url: str, timeout: float = 6.0) -> str | None:
        """Best-effort: try a handful of candidates and return the first that
        can actually reach test_url. Returns None if nothing works quickly."""
        self._refresh()
        pool = self._good + self._proxies
        random.shuffle(pool)
        for raw in pool[:15]:
            proxy_url = raw if "://" in raw else f"http://{raw}"
            try:
                with httpx.Client(proxy=proxy_url, timeout=timeout) as client:
                    r = client.get(test_url)
                    if r.status_code < 500:
                        if raw not in self._good:
                            self._good.append(raw)
                        return proxy_url
            except Exception:
                continue
        return None


pool = ProxyPool()
