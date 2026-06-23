import logging
from datetime import datetime

from telegram.ext import Application

from db import repository as repo

logger = logging.getLogger(__name__)


async def check_birthdays(application: Application) -> None:
    tz = application.bot_data["timezone"]
    session_factory = application.bot_data["session_factory"]

    now = datetime.now(tz)
    current_hhmm = now.strftime("%H:%M")
    today = now.date()

    session = session_factory()
    try:
        subscriptions = repo.get_due_subscriptions(session, current_hhmm, today)
        if not subscriptions:
            return

        logger.info(
            "Found %d due subscription(s) at %s",
            len(subscriptions),
            current_hhmm,
        )

        for sub in subscriptions:
            name = sub.person.name
            if sub.person.custom_message:
                msg = sub.person.custom_message.replace("{name}", name)
                text = f"🎉 {msg} 🎂"
            else:
                text = f"🎉 Hoy es el cumpleaños de {name}! 🎂"

            try:
                await application.bot.send_message(chat_id=sub.subscriber_tg_id, text=text)
                sub.last_notified_date = today
                session.commit()
                logger.info("Sent birthday reminder for %s", name)
            except Exception:
                logger.exception("Failed to send reminder for %s", name)
    finally:
        session.close()
