import logging
import os
from zoneinfo import ZoneInfo

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import create_engine, event, inspect, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker
from telegram import BotCommand, Update
from telegram.ext import Application, CommandHandler

from db.models import Base
from bot.handlers import (
    add_birthday,
    help_command,
    list_birthdays,
    my_subscriptions,
    remove_birthday,
    set_message,
    set_time,
    start,
    subscribe,
    subscribe_all,
    unsubscribe,
)
from bot.scheduler import check_birthdays

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


async def post_init(application: Application) -> None:
    await application.bot.set_my_commands([
        BotCommand("start", "Welcome message and help"),
        BotCommand("add_birthday", "Register a birthday [name] [YYYY-MM-DD]"),
        BotCommand("remove_birthday", "Remove a registered birthday [name]"),
        BotCommand("list_birthdays", "Show all registered birthdays"),
        BotCommand("subscribe", "Subscribe to someone [name]"),
        BotCommand("subscribe_all", "Subscribe to all public birthdays"),
        BotCommand("unsubscribe", "Unsubscribe from someone [name]"),
        BotCommand("my_subscriptions", "List your subscriptions"),
        BotCommand("set_message", "Set a custom message [name] -- [msg]"),
        BotCommand("set_time", "Set your notification time [HH:MM]"),
        BotCommand("help", "Show all commands and usage"),
    ])
    scheduler = application.bot_data["scheduler"]
    scheduler.start()
    logger.info("Bot started")


def main() -> None:
    BOT_TOKEN = os.environ["BOT_TOKEN"]
    TZ = os.environ.get("TZ", "America/Santiago")

    engine = create_engine(
        "sqlite:///data/birthdays.db",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(engine)

    inspector = inspect(engine)
    if "is_private" not in [c["name"] for c in inspector.get_columns("persons")]:
        with engine.connect() as conn:
            conn.execute(text("ALTER TABLE persons ADD COLUMN is_private BOOLEAN DEFAULT 0"))
            conn.commit()

    session_factory = sessionmaker(bind=engine)

    application = (
        Application.builder()
        .token(BOT_TOKEN)
        .post_init(post_init)
        .build()
    )

    scheduler = AsyncIOScheduler(timezone=ZoneInfo(TZ))
    scheduler.add_job(
        check_birthdays,
        "interval",
        seconds=60,
        args=[application],
        id="birthday_check",
        replace_existing=True,
    )

    application.bot_data["scheduler"] = scheduler
    application.bot_data["session_factory"] = session_factory
    application.bot_data["timezone"] = ZoneInfo(TZ)

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("add_birthday", add_birthday))
    application.add_handler(CommandHandler("remove_birthday", remove_birthday))
    application.add_handler(CommandHandler("list_birthdays", list_birthdays))
    application.add_handler(CommandHandler("subscribe", subscribe))
    application.add_handler(CommandHandler("subscribe_all", subscribe_all))
    application.add_handler(CommandHandler("unsubscribe", unsubscribe))
    application.add_handler(CommandHandler("my_subscriptions", my_subscriptions))
    application.add_handler(CommandHandler("set_message", set_message))
    application.add_handler(CommandHandler("set_time", set_time))

    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
