import logging

from ticketbot.checkers import CheckResult
from ticketbot.currency import rub_to_uzs
from ticketbot.net import request_with_fallback

logger = logging.getLogger(__name__)

SEARCH_URL = "https://api.aerotur.aero/api/flights"

HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json",
    "Origin": "https://uzairways.online",
    "Referer": "https://uzairways.online/",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/122.0 Safari/537.36",
}


async def check_flights(from_code: str, to_code: str, date_str: str) -> CheckResult:
    body = {
        "locale": "ru",
        "instance": "uzairways.online.dev",
        "adults": 1,
        "children": 0,
        "infants": 0,
        "infants_seat": 0,
        "flight_class": "Economy",
        "from": from_code,
        "fromType": "city",
        "to": to_code,
        "toType": "city",
        "aroundDates": 0,
        "date1": date_str,
        "date2": None,
        "asGrouped": 0,
    }
    try:
        resp = await request_with_fallback("POST", SEARCH_URL, headers=HEADERS, json=body)
    except Exception as exc:
        return CheckResult(available=False, error=str(exc))

    if resp.status_code != 200:
        return CheckResult(available=False, error=f"HTTP {resp.status_code}")

    try:
        data = resp.json()
    except Exception:
        return CheckResult(available=False, error="Noto'g'ri javob formati")

    variants = data.get("variants") or []
    if not variants:
        return CheckResult(available=False)

    variants = sorted(variants, key=lambda v: v.get("price", float("inf")))
    lines = []
    for v in variants[:3]:
        price = v.get("price")
        currency = v.get("currency", "")
        if currency == "RUB" and price is not None:
            price_text = f"{await rub_to_uzs(price):,} so'm".replace(",", " ")
        elif currency == "UZS" and price is not None:
            price_text = f"{price:,} so'm".replace(",", " ")
        else:
            price_text = f"{price} {currency}"
        legs = v.get("legs") or []
        seg = (legs[0]["segments"][0] if legs and legs[0].get("segments") else {})
        flight_no = seg.get("flight_number_full", "?")
        dep_time = seg.get("departure_date_time", "")
        arr_time = seg.get("arrival_date_time", "")
        dep_ap = seg.get("departure_airport", from_code)
        arr_ap = seg.get("arrival_airport", to_code)
        booking_url = v.get("booking_url", "")
        lines.append(
            f"✈️ {flight_no}: {dep_ap} {dep_time} → {arr_ap} {arr_time}\n"
            f"   Narxi: {price_text}\n"
            f"   {booking_url}"
        )

    return CheckResult(available=True, summary="\n\n".join(lines))
