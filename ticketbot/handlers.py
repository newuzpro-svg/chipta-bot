import logging

from telegram import Update
from telegram.ext import (
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

from ticketbot import db, texts
from ticketbot.checkers.flights import check_flights
from ticketbot.checkers.trains import check_trains
from ticketbot.cities import flight_city_name, train_station_name
from ticketbot.keyboards import (
    city_keyboard,
    confirm_keyboard,
    date_keyboard,
    kind_keyboard,
    main_menu_keyboard,
    subs_keyboard,
)

logger = logging.getLogger(__name__)

CHOOSE_KIND, CHOOSE_FROM, CHOOSE_TO, CHOOSE_DATE, CONFIRM = range(5)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(texts.WELCOME, reply_markup=main_menu_keyboard())


async def add_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.clear()
    await update.message.reply_text(texts.CHOOSE_KIND, reply_markup=kind_keyboard())
    return CHOOSE_KIND


async def choose_kind(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    kind = query.data.split(":", 1)[1]
    context.user_data["kind"] = kind
    await query.edit_message_text(texts.CHOOSE_FROM, reply_markup=city_keyboard(kind, "from"))
    return CHOOSE_FROM


async def choose_from(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    code = query.data.split(":", 1)[1]
    kind = context.user_data["kind"]
    name = flight_city_name(code) if kind == "flight" else train_station_name(code)
    context.user_data["from_code"] = code
    context.user_data["from_name"] = name
    await query.edit_message_text(
        texts.CHOOSE_TO, reply_markup=city_keyboard(kind, "to", exclude_code=code)
    )
    return CHOOSE_TO


async def choose_to(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    code = query.data.split(":", 1)[1]
    kind = context.user_data["kind"]
    if code == context.user_data.get("from_code"):
        await query.answer(texts.SAME_CITY, show_alert=True)
        return CHOOSE_TO
    name = flight_city_name(code) if kind == "flight" else train_station_name(code)
    context.user_data["to_code"] = code
    context.user_data["to_name"] = name
    await query.edit_message_text(texts.CHOOSE_DATE, reply_markup=date_keyboard())
    return CHOOSE_DATE


async def choose_date(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    travel_date = query.data.split(":", 1)[1]
    context.user_data["date"] = travel_date
    ud = context.user_data
    text = (
        f"Tekshirib ko'ring:\n\n"
        f"{'✈️' if ud['kind'] == 'flight' else '🚆'} {ud['from_name']} → {ud['to_name']}\n"
        f"📅 {travel_date}\n\n"
        f"Shu yo'nalishni kuzatishni boshlaymizmi?"
    )
    await query.edit_message_text(text, reply_markup=confirm_keyboard())
    return CONFIRM


async def confirm(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    if query.data.endswith(":no"):
        await query.edit_message_text(texts.CANCELLED)
        context.user_data.clear()
        return ConversationHandler.END

    ud = context.user_data
    await query.edit_message_text(texts.SEARCHING)

    if ud["kind"] == "flight":
        result = await check_flights(ud["from_code"], ud["to_code"], ud["date"])
    else:
        result = await check_trains(ud["from_name"], ud["to_name"], ud["date"])

    if result.available:
        await query.edit_message_text(
            texts.FOUND_NOW.format(
                from_name=ud["from_name"], to_name=ud["to_name"],
                date=ud["date"], summary=result.summary,
            )
        )
    else:
        db.add_subscription(
            chat_id=update.effective_chat.id,
            kind=ud["kind"],
            from_code=ud["from_code"],
            from_name=ud["from_name"],
            to_code=ud["to_code"],
            to_name=ud["to_name"],
            travel_date=ud["date"],
        )
        await query.edit_message_text(
            texts.STARTED_WATCHING.format(
                from_name=ud["from_name"], to_name=ud["to_name"], date=ud["date"],
            )
        )
    context.user_data.clear()
    return ConversationHandler.END


async def cancel_conversation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.clear()
    await update.message.reply_text(texts.CANCELLED)
    return ConversationHandler.END


async def contact(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(texts.CONTACT_TEXT)


async def my_subs(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    subs = db.list_user_subscriptions(update.effective_chat.id)
    if not subs:
        await update.message.reply_text(texts.NO_SUBS)
        return
    await update.message.reply_text(texts.SUBS_HEADER, reply_markup=subs_keyboard(subs))


async def cancel_sub(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    sub_id = int(query.data.split(":", 1)[1])
    sub = db.get_subscription(sub_id)
    if sub and sub["chat_id"] == update.effective_chat.id:
        db.deactivate_subscription(sub_id)
        await query.edit_message_text(texts.CANCELLED)
    else:
        await query.edit_message_text("Topilmadi.")


def build_conversation_handler() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[
            CommandHandler("add", add_start),
            MessageHandler(filters.Text([texts.MENU_ADD]), add_start),
        ],
        states={
            CHOOSE_KIND: [CallbackQueryHandler(choose_kind, pattern=r"^kind:")],
            CHOOSE_FROM: [CallbackQueryHandler(choose_from, pattern=r"^from:")],
            CHOOSE_TO: [CallbackQueryHandler(choose_to, pattern=r"^to:")],
            CHOOSE_DATE: [CallbackQueryHandler(choose_date, pattern=r"^date:")],
            CONFIRM: [CallbackQueryHandler(confirm, pattern=r"^confirm:")],
        },
        fallbacks=[CommandHandler("cancel", cancel_conversation)],
    )
