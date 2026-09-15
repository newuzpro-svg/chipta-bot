import logging
import os
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from telegram.ext import Application, CallbackQueryHandler, CommandHandler, MessageHandler, filters

from ticketbot import db, handlers, texts
from ticketbot.config import BOT_TOKEN, CHECK_INTERVAL_MINUTES
from ticketbot.monitor import check_all_subscriptions

logging.basicConfig(
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    level=logging.INFO,
)
logging.getLogger("httpx").setLevel(logging.WARNING)


class _HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")

    def log_message(self, format, *args) -> None:  # silence per-request logging
        pass


def _start_health_server() -> None:
    """Render (and similar free hosts) require a web service to bind $PORT
    and expects it to answer health checks, or it puts the instance to sleep."""
    port = int(os.environ.get("PORT", "8080"))
    server = ThreadingHTTPServer(("0.0.0.0", port), _HealthHandler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    logging.getLogger(__name__).info("Health-check server %s portda ishga tushdi", port)


def main() -> None:
    db.init_db()
    _start_health_server()

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", handlers.start))
    app.add_handler(handlers.build_conversation_handler())
    app.add_handler(CommandHandler("mysubs", handlers.my_subs))
    app.add_handler(MessageHandler(filters.Text([texts.MENU_SUBS]), handlers.my_subs))
    app.add_handler(MessageHandler(filters.Text([texts.MENU_CONTACT]), handlers.contact))
    app.add_handler(CallbackQueryHandler(handlers.cancel_sub, pattern=r"^cancel:"))

    app.job_queue.run_repeating(
        check_all_subscriptions,
        interval=CHECK_INTERVAL_MINUTES * 60,
        first=15,
    )

    logger = logging.getLogger(__name__)
    logger.info("Bot ishga tushdi, tekshirish oralig'i: %s daqiqa", CHECK_INTERVAL_MINUTES)
    app.run_polling()


if __name__ == "__main__":
    main()
