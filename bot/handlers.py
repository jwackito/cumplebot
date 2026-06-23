from datetime import datetime

from telegram import Update
from telegram.ext import ContextTypes

from db import repository as repo


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tg_id = update.effective_user.id
    session = context.bot_data["session_factory"]()
    try:
        repo.ensure_user(session, tg_id)
    finally:
        session.close()

    await update.message.reply_text(
        "Welcome to CumpleBot! 🎂\n\n"
        "I help manage and remind about birthdays.\n"
        "Send me a message to get started, and I'll notify you privately when someone's birthday arrives.\n\n"
        "Commands:\n"
        "/add_birthday <name> <YYYY-MM-DD> [message] - Register a birthday (use --private to restrict)\n"
        "/remove_birthday <name> - Remove a registered birthday\n"
        "/list_birthdays - Show all registered birthdays\n"
        "/subscribe <name> - Subscribe to someone's birthday reminders\n"
        "/unsubscribe <name> - Unsubscribe from someone's birthday\n"
        "/my_subscriptions - List your subscriptions\n"
        "/set_message <name> <message> - Set a custom message for a birthday\n"
        "/set_time <HH:MM> - Set your preferred notification time (24h)\n"
        "/subscribe_all - Subscribe to all public birthdays\n"
        "/help - Show this help"
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await start(update, context)


async def subscribe_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tg_id = update.effective_user.id
    session = context.bot_data["session_factory"]()
    try:
        repo.ensure_user(session, tg_id)
        repo.get_or_create_user_preference(session, tg_id)
        public_persons = repo.get_public_persons(session)
        if not public_persons:
            await update.message.reply_text("No public birthdays available to subscribe to.")
            return

        count = 0
        for person in public_persons:
            existing = repo.get_subscription(session, tg_id, person.id)
            if not existing:
                repo.add_subscription(session, tg_id, person.id)
                count += 1

        await update.message.reply_text(
            f"Subscribed to {count} public birthday(s) out of {len(public_persons)}! 🎉"
        )
    finally:
        session.close()


async def add_birthday(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args or len(context.args) < 2:
        await update.message.reply_text("Usage: /add_birthday <name> <YYYY-MM-DD> [message]")
        return

    is_private = "--private" in context.args
    args = [a for a in context.args if a != "--private"]

    if len(args) < 2:
        await update.message.reply_text("Usage: /add_birthday <name> <YYYY-MM-DD> [message]")
        return

    date_idx = None
    for i, arg in enumerate(args):
        try:
            datetime.strptime(arg, "%Y-%m-%d")
            date_idx = i
            break
        except ValueError:
            continue

    if date_idx is None:
        await update.message.reply_text("Missing valid date. Use YYYY-MM-DD (e.g. 1990-01-15)")
        return

    name = " ".join(args[:date_idx])
    date_str = args[date_idx]
    message = " ".join(args[date_idx + 1:]) or None

    try:
        birthday = datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        await update.message.reply_text("Invalid date format. Use YYYY-MM-DD (e.g. 1990-01-15)")
        return

    tg_id = update.effective_user.id
    session = context.bot_data["session_factory"]()
    try:
        existing = repo.get_person(session, name)
        if existing:
            await update.message.reply_text(f"{name} is already registered.")
            return

        repo.ensure_user(session, tg_id)
        person = repo.add_person(session, name, birthday, tg_id, message, is_private=is_private)

        if is_private:
            repo.add_subscription(session, tg_id, person.id)
            repo.get_or_create_user_preference(session, tg_id)
            await update.message.reply_text(
                f"Birthday registered privately for {name} ({birthday.strftime('%d %B %Y')})! 🎉\n"
                "Only you are subscribed."
            )
        else:
            repo.auto_subscribe_all(session, person.id, exclude_tg_id=tg_id)
            repo.add_subscription(session, tg_id, person.id)
            repo.get_or_create_user_preference(session, tg_id)
            await update.message.reply_text(
                f"Birthday registered for {name} ({birthday.strftime('%d %B %Y')})! 🎉\n"
                "All users have been auto-subscribed."
            )
    finally:
        session.close()


async def remove_birthday(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /remove_birthday <name>")
        return

    name = " ".join(context.args)
    session = context.bot_data["session_factory"]()
    try:
        person = repo.remove_person(session, name)
        if person:
            await update.message.reply_text(f"{name} has been removed. 🗑️")
        else:
            await update.message.reply_text(f"No birthday found for {name}.")
    finally:
        session.close()


async def list_birthdays(update: Update, context: ContextTypes.DEFAULT_TYPE):
    session = context.bot_data["session_factory"]()
    try:
        persons = repo.get_all_persons(session)
        if not persons:
            await update.message.reply_text("No birthdays registered yet.")
            return

        lines = ["Registered birthdays:\n"]
        for p in sorted(persons, key=lambda x: (x.birthday.month, x.birthday.day)):
            msg = f" - {p.name}: {p.birthday.strftime('%d %B')}"
            if p.custom_message:
                msg += f"  ({p.custom_message})"
            lines.append(msg)
        await update.message.reply_text("\n".join(lines))
    finally:
        session.close()


async def subscribe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /subscribe <name>")
        return

    name = " ".join(context.args)
    tg_id = update.effective_user.id
    session = context.bot_data["session_factory"]()
    try:
        person = repo.get_person(session, name)
        if not person:
            await update.message.reply_text(f"No birthday found for {name}.")
            return

        existing = repo.get_subscription(session, tg_id, person.id)
        if existing:
            await update.message.reply_text(f"You are already subscribed to {name}.")
            return

        repo.add_subscription(session, tg_id, person.id)
        repo.get_or_create_user_preference(session, tg_id)
        await update.message.reply_text(
            f"You are now subscribed to {name}'s birthday reminders! 🎉"
        )
    finally:
        session.close()


async def unsubscribe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /unsubscribe <name>")
        return

    name = " ".join(context.args)
    tg_id = update.effective_user.id
    session = context.bot_data["session_factory"]()
    try:
        person = repo.get_person(session, name)
        if not person:
            await update.message.reply_text(f"No birthday found for {name}.")
            return

        sub = repo.remove_subscription(session, tg_id, person.id)
        if sub:
            await update.message.reply_text(f"Unsubscribed from {name}.")
        else:
            await update.message.reply_text(f"You were not subscribed to {name}.")
    finally:
        session.close()


async def my_subscriptions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tg_id = update.effective_user.id
    session = context.bot_data["session_factory"]()
    try:
        subs = repo.get_subscriptions_for_user(session, tg_id)
        if not subs:
            await update.message.reply_text("You are not subscribed to anyone.")
            return

        pref = repo.get_or_create_user_preference(session, tg_id)
        lines = [f"Your subscriptions (notification time: {pref.notification_time}):\n"]
        for s in subs:
            bday = s.person.birthday.strftime("%d %B")
            lines.append(f" - {s.person.name} ({bday})")
        await update.message.reply_text("\n".join(lines))
    finally:
        session.close()


async def set_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args or len(context.args) < 2:
        await update.message.reply_text("Usage: /set_message <name> -- <message>")
        return

    if "--" in context.args:
        sep_idx = context.args.index("--")
        name = " ".join(context.args[:sep_idx])
        message = " ".join(context.args[sep_idx + 1:])
    else:
        name = context.args[0]
        message = " ".join(context.args[1:])

    if not name or not message:
        await update.message.reply_text("Usage: /set_message <name> -- <message>")
        return

    session = context.bot_data["session_factory"]()
    try:
        person = repo.get_person(session, name)
        if not person:
            await update.message.reply_text(f"No birthday found for {name}.")
            return

        person.custom_message = message
        session.commit()
        await update.message.reply_text(f"Birthday message for {name} has been set! 🎉")
    finally:
        session.close()


async def set_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args or len(context.args) != 1:
        await update.message.reply_text("Usage: /set_time <HH:MM> (e.g. /set_time 09:00)")
        return

    time_str = context.args[0]
    try:
        datetime.strptime(time_str, "%H:%M")
    except ValueError:
        await update.message.reply_text("Invalid time format. Use HH:MM in 24h format (e.g. 09:00, 14:30).")
        return

    tg_id = update.effective_user.id
    session = context.bot_data["session_factory"]()
    try:
        repo.set_notification_time(session, tg_id, time_str)
        await update.message.reply_text(f"Your notification time has been set to {time_str}.")
    finally:
        session.close()
