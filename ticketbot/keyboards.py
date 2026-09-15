from datetime import date, timedelta

from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)

from ticketbot.cities import FLIGHT_CITIES, TRAIN_STATIONS
from ticketbot.texts import MENU_ADD, MENU_CONTACT, MENU_SUBS, MONTHS_UZ, WEEKDAYS_UZ


def main_menu_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        [
            [KeyboardButton(MENU_ADD), KeyboardButton(MENU_SUBS)],
            [KeyboardButton(MENU_CONTACT)],
        ],
        resize_keyboard=True,
        is_persistent=True,
    )


def kind_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✈️ Aviabilet", callback_data="kind:flight")],
        [InlineKeyboardButton("🚆 Poezd bilet", callback_data="kind:train")],
    ])


def _city_rows(cities: list[dict], prefix: str, exclude_code: str | None = None):
    rows = []
    row = []
    for c in cities:
        if c["code"] == exclude_code:
            continue
        row.append(InlineKeyboardButton(c["name"], callback_data=f"{prefix}:{c['code']}"))
        if len(row) == 2:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    return rows


def city_keyboard(kind: str, prefix: str, exclude_code: str | None = None) -> InlineKeyboardMarkup:
    cities = FLIGHT_CITIES if kind == "flight" else TRAIN_STATIONS
    return InlineKeyboardMarkup(_city_rows(cities, prefix, exclude_code))


def date_keyboard(days_ahead: int = 14) -> InlineKeyboardMarkup:
    today = date.today()
    rows = []
    row = []
    for i in range(days_ahead):
        d = today + timedelta(days=i)
        label = f"{d.day} {MONTHS_UZ[d.month - 1]} ({WEEKDAYS_UZ[d.weekday()]})"
        row.append(InlineKeyboardButton(label, callback_data=f"date:{d.isoformat()}"))
        if len(row) == 2:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    return InlineKeyboardMarkup(rows)


def confirm_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Ha, kuzat", callback_data="confirm:yes"),
            InlineKeyboardButton("❌ Bekor qilish", callback_data="confirm:no"),
        ]
    ])


def subs_keyboard(subs) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(
            f"❌ {s['from_name']} → {s['to_name']} ({s['travel_date']})",
            callback_data=f"cancel:{s['id']}",
        )]
        for s in subs
    ]
    return InlineKeyboardMarkup(rows)
