import logging
import re
from datetime import date

from playwright.async_api import async_playwright

from ticketbot.checkers import CheckResult

logger = logging.getLogger(__name__)

HOME_URL = "https://eticket.railway.uz/uz"
SEARCH_API_PATH = "/api/v3/handbook/trains/list"

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/122.0 Safari/537.36"
)

# eticket.railway.uz sits behind bot-protection that rejects plain HTTP
# clients (fails even with the exact headers/cookies a real browser sends),
# so unlike the flight checker this one drives a real headless browser and
# reads the search API response straight off the network, instead of
# scraping rendered HTML.


async def check_trains(from_name: str, to_name: str, date_str: str) -> CheckResult:
    target = date.fromisoformat(date_str)
    today = date.today()
    months_ahead = (target.year - today.year) * 12 + (target.month - today.month)
    if months_ahead <= 1:
        clicks_needed, panel_index = 0, max(months_ahead, 0)
    else:
        clicks_needed, panel_index = months_ahead - 1, 1

    captured: dict = {}

    async def on_response(resp):
        if SEARCH_API_PATH in resp.url and resp.request.method == "POST":
            try:
                captured["body"] = await resp.json()
            except Exception:
                pass

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page(user_agent=USER_AGENT)
            page.on("response", on_response)
            try:
                await page.goto(HOME_URL, wait_until="load", timeout=45000)
                await page.wait_for_timeout(2500)

                await page.get_by_text("QAYERDAN", exact=False).first.click()
                await page.wait_for_timeout(700)
                await page.get_by_role("option", name=from_name, exact=True).first.click(force=True)
                await page.wait_for_timeout(700)
                await page.get_by_role("option", name=to_name, exact=True).first.click(force=True)
                await page.wait_for_timeout(700)

                for _ in range(clicks_needed):
                    await page.get_by_label("Next month").click()
                    await page.wait_for_timeout(300)

                day_pattern = re.compile(rf"^{target.day}$")
                panels = page.locator(".ngb-dp-month")
                if await panels.count() > panel_index:
                    scope = panels.nth(panel_index)
                else:
                    scope = page
                day_cell = scope.locator(
                    "div[ngbdatepickerdayview]:not(.outside)", has_text=day_pattern
                ).first
                await day_cell.click(force=True, timeout=10000)
                await page.wait_for_timeout(1500)

                search_btn = page.get_by_text("IZLASH", exact=False)
                if await search_btn.count() > 0:
                    try:
                        await search_btn.first.click(force=True, timeout=3000)
                    except Exception:
                        pass

                await page.wait_for_timeout(3000)
            finally:
                await browser.close()
    except Exception as exc:
        logger.warning("Train search automation failed: %s", exc)
        return CheckResult(available=False, error=str(exc))

    if "body" not in captured:
        return CheckResult(available=False, error="Sayt javob bermadi (sekin yoki bloklagan)")

    trains = (
        captured["body"].get("data", {})
        .get("directions", {})
        .get("forward", {})
        .get("trains", [])
        or []
    )

    lines = []
    for t in trains:
        cars = t.get("cars") or []
        total_free = sum(c.get("freeSeats", 0) for c in cars)
        if total_free <= 0:
            continue
        number = t.get("number", "?")
        brand = t.get("brand", "")
        dep_date = t.get("departureDate", "")
        arr_date = t.get("arrivalDate", "")
        car_bits = []
        for c in cars:
            if c.get("freeSeats", 0) <= 0:
                continue
            tariffs = c.get("tariffs") or []
            price = tariffs[0].get("tariff") if tariffs else None
            price_txt = f", {price:,} so'm".replace(",", " ") if price else ""
            car_bits.append(f"{c.get('type', '?')}: {c.get('freeSeats', 0)} joy{price_txt}")
        lines.append(
            f"🚆 {number} ({brand}): {dep_date} → {arr_date}\n"
            f"   {'; '.join(car_bits)}"
        )

    if not lines:
        return CheckResult(available=False)

    return CheckResult(available=True, summary="\n\n".join(lines))
