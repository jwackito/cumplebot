# CumpleBot

A Telegram bot that registers birthdays and sends private reminders to subscribers. Runs in Docker.

## Features

- Register birthdays with multi-word names (e.g. `Joaquin Bogado`)
- Private and public birthdays (`--private` flag)
- Per-user notification time (each subscriber chooses when to be reminded)
- Custom birthday messages with `{name}` placeholder
- Auto-subscribe all users on public birthdays
- Per-person subscriptions (subscribe/unsubscribe per person)
- Automatic daily check every 60 seconds
- SQLite persistence via Docker volume

## Quick Start

```bash
# 1. Clone and configure
git clone git@github.com:jwackito/cumplebot.git
cd cumplebot
cp .env.example .env
# Edit .env with your BOT_TOKEN and TZ

# 2. Run
docker compose up -d
```

## Configuration

| Variable | Description | Default |
|---|---|---|
| `BOT_TOKEN` | Telegram bot token from @BotFather | required |
| `TZ` | Timezone for reminders | `America/Argentina/Buenos_Aires` |

## Commands

| Command | Description |
|---|---|
| `/start` | Welcome message and help |
| `/add_birthday` | Register a birthday `[name] [YYYY-MM-DD] [--private]` |
| `/remove_birthday` | Remove a registered birthday `[name]` |
| `/list_birthdays` | Show all registered birthdays |
| `/subscribe` | Subscribe to someone `[name]` |
| `/subscribe_all` | Subscribe to all public birthdays |
| `/unsubscribe` | Unsubscribe from someone `[name]` |
| `/my_subscriptions` | List your subscriptions |
| `/set_message` | Set a custom message `[name] -- [message]` |
| `/set_time` | Set your notification time `[HH:MM]` |
| `/help` | Show all commands |

## Examples

```text
/add_birthday Joaquin Bogado 1983-07-27
→ Registered publicly, all users auto-subscribed

/add_birthday Joaquin Bogado 1983-07-27 --private Happy birthday {name}!
→ Registered privately, only you subscribed with a custom message

/subscribe Joaquin Bogado
→ Subscribe to Joaquin's birthday reminders

/set_time 09:00
→ Get reminded at 9 AM

/set_message Joaquin Bogado -- Happy {name} day!
→ Custom message with name placeholder
```

## Development

Changes to `bot/` and `db/` are automatically reloaded inside the container via `watchfiles` — no rebuild needed.

## License

GNU General Public License v3.0
