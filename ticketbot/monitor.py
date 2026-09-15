import asyncio
import logging

from telegram.ext import ContextTypes

from ticketbot import db
from ticketbot.checkers.flights import check_flights
from ticketbot.checkers.trains import check_trains

logger = logging.getLogger(__name__)

DELAY_BETWEEN_CHECKS_SECONDS = 3


async def check_all_subscriptions(context: ContextTypes.DEFAULT_TYPE) -> None:
    subs = db.list_active_subscriptions()
    if not subs:
        return
    logger.info("Checking %d active subscription(s)", len(subs))

    for sub in subs:
        try:
            if sub["kind"] == "flight":
                result = await check_flights(sub["from_code"], sub["to_code"], sub["travel_date"])
            else:
                result = await check_trains(sub["from_name"], sub["to_name"], sub["travel_date"])
        except Exception as exc:
            logger.exception("Unexpected error checking subscription %s", sub["id"])
            db.mark_checked(sub["id"], error=str(exc))
            await asyncio.sleep(DELAY_BETWEEN_CHECKS_SECONDS)
            continue

        if result.error:
            db.mark_checked(sub["id"], error=result.error)
            logger.warning("Subscription %s check failed: %s", sub["id"], result.error)
        elif result.available:
            db.mark_checked(sub["id"])
            db.deactivate_subscription(sub["id"])
            emoji = "✈️" if sub["kind"] == "flight" else "🚆"
            text = (
                f"🎉 Chipta chiqdi! {emoji} {sub['from_name']} → {sub['to_name']} "
                f"({sub['travel_date']})\n\n{result.summary}"
            )
            try:
                await context.bot.send_message(chat_id=sub["chat_id"], text=text)
            except Exception:
                logger.exception("Failed to notify chat %s", sub["chat_id"])
        else:
            db.mark_checked(sub["id"])

        await asyncio.sleep(DELAY_BETWEEN_CHECKS_SECONDS)
