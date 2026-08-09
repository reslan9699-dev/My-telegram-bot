# Protected File Distribution Bot

A production-ready Telegram bot built with **Python 3.12** and **aiogram v3** that lets a single
admin upload files, publish a post to a public channel, and only lets users download the files
after they join every required channel.

Files are **never downloaded or stored on disk** — only Telegram `file_id`s are persisted, so the
bot has no file storage and can resend media at any time.

---

## Features

- **Admin panel** with `Upload New Post`, `Cancel Current Upload` and `Statistics` buttons.
- **Multi-file upload flow** (FSM driven): PDF, ZIP, RAR, MP4, MP3, photos, documents and any
  Telegram-supported media. Files are kept in memory as `file_id`s until publishing.
- **Two-step post creation**: files first, then the post (text or photo + caption).
- **Automatic publishing** to a public channel with an inline **Download** button
  (`download_<post_id>` callback).
- **Membership gate**: users must join every channel listed in `REQUIRED_CHANNELS`
  (verified with `getChatMember`) before files are delivered.
- **Join prompt** with per-channel `Join Channel N` URL buttons and an `I've Joined` re-check button.
- **Download delivery** straight to the user's private chat, with a live progress message
  (`Sending files... 3/15 completed...`).
- **Bonus hardening**:
  - duplicate-download protection (per-user/per-post lock),
  - user rate limiting (sliding window),
  - admin statistics (total posts, files, downloads),
  - temporary upload sessions cleared after publishing/cancelling,
  - HTML-safe message formatting,
  - membership check caching (successes only) to reduce API calls,
  - comprehensive logging (uploads, downloads, errors, membership failures).

---

## Tech stack

| Layer      | Technology                                  |
|------------|---------------------------------------------|
| Language   | Python 3.12                                 |
| Framework  | aiogram 3.x (async)                         |
| Database   | SQLite via SQLAlchemy 2.0 (async)           |
| Migrations | Alembic                                     |
| Config     | python-dotenv + `config.py`                 |
| Runtime    | Docker / docker-compose                     |
| State      | FSM (aiogram `MemoryStorage`)               |

> SQLite can be swapped for PostgreSQL later by setting
> `DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/dbname` and installing `asyncpg`.

---

## Project structure

```
.
├── bot.py                  # Entrypoint: builds Dispatcher, starts polling
├── config.py               # Typed settings loaded from .env
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── .env.example
├── alembic.ini
├── migrations/             # Alembic migrations
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
│       └── 0001_initial.py
├── database/
│   ├── database.py         # Async engine, session factory, Base
│   └── models.py           # Post, File, DownloadLog
├── handlers/
│   ├── admin.py            # Admin panel + upload flow
│   ├── user.py             # User private-chat entry points
│   ├── callbacks.py        # download_ / verify_ callbacks, delivery
│   └── middlewares.py      # RateLimitMiddleware
├── keyboards/
│   ├── inline.py           # Download + join-channel keyboards
│   └── reply.py            # Admin reply keyboard
├── services/
│   ├── membership.py       # getChatMember checks + cache
│   ├── publisher.py        # Publishes posts to the channel
│   └── storage.py          # Temp upload sessions + DB operations
├── states.py               # FSM states (Idle, ReceivingFiles, WaitingPost, Publishing)
└── utils.py                # Media extraction, HTML escaping, file sending
```

---

## Prerequisites

- Python 3.12 (or Docker with docker-compose)
- A Telegram account

---

## Setup

### 1. Create a bot with BotFather

1. Open Telegram and message [@BotFather](https://t.me/BotFather).
2. Send `/newbot`, choose a display name and a username ending in `bot`.
3. Copy the **token** (format `123456789:AAF...`) — this is `BOT_TOKEN`.

### 2. Obtain your ADMIN_ID

Your Telegram user id is a numeric id, e.g. `123456789`.

Options:

- Message [@userinfobot](https://t.me/userinfobot) and read your `Id`.
- Or: message your own bot `/start`, then call
  `https://api.telegram.org/bot<BOT_TOKEN>/getUpdates` in a browser and read the `from.id` value.

This id goes into `ADMIN_ID`. Only this user can access the admin panel.

### 3. Create the public channel

1. Telegram menu → **New Channel** → give it a name.
2. Set the channel as **Public** and choose a short username (e.g. `my_public_channel`).
3. The channel handle (e.g. `@my_public_channel`) is `CHANNEL_ID`.

### 4. Add the bot as an admin to the channel

1. Open the channel → **Edit** (pencil) → **Administrators**.
2. Add your bot (search its username).
3. Grant at least **Post Messages** permission (for private channels also grant invite management).
4. Press Save. The bot can now publish posts.

### 5. Configure required channels

List the public channels users must join **before** downloading, comma separated:

```
REQUIRED_CHANNELS=@channel1,@channel2,@channel3
```

The bot must be a member of each required channel (or an admin) so it can verify memberships.

### 6. Create the `.env` file

```bash
cp .env.example .env
```

Fill in `BOT_TOKEN`, `ADMIN_ID`, `CHANNEL_ID` and `REQUIRED_CHANNELS`.

| Variable                    | Description                                              | Example                          |
|-----------------------------|----------------------------------------------------------|----------------------------------|
| `BOT_TOKEN`                 | Token from BotFather                                     | `123456789:AAF...`               |
| `ADMIN_ID`                  | Numeric Telegram id of the single admin                  | `123456789`                      |
| `CHANNEL_ID`                | Public channel to publish into (handle or numeric id)    | `@my_public_channel`             |
| `REQUIRED_CHANNELS`         | Comma-separated channels users must join                 | `@c1,@c2`                        |
| `DATABASE_URL`              | SQLAlchemy async URL                                     | `sqlite+aiosqlite:///./bot.db`   |
| `LOG_LEVEL`                 | `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`          | `INFO`                           |
| `RATE_LIMIT_MAX`            | Max user actions per window                              | `20`                             |
| `RATE_LIMIT_WINDOW`         | Rate limit window in seconds                             | `30`                             |
| `MEMBERSHIP_CACHE_TTL`      | Cache TTL (seconds) for successful membership checks     | `60`                             |
| `PROGRESS_UPDATE_INTERVAL`  | Refresh the download progress message every N files      | `3`                              |

---

## Run locally

```bash
# 1. Create a virtual environment
python -m venv .venv

# Windows
.venv\Scripts\activate
# Linux / macOS
source .venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Apply database migrations
alembic upgrade head

# 4. Start the bot
python bot.py
```

Logs will show the bot username once polling starts.

---

## Run with Docker

Make sure `.env` exists first (see step 6 above), then:

```bash
docker compose up --build
```

The compose file runs `alembic upgrade head && python bot.py` on startup and persists
`bot.db` on the host so data survives container restarts.

Stop with `Ctrl+C` or `docker compose down`.

---

## Usage

### Admin

1. Send `/start` to the bot — the admin panel appears (reply keyboard).
2. Press **Upload New Post**.
3. Send any number of files. Each one replies `File added. Current files: N`.
   Supported: PDF, ZIP, RAR, MP4, MP3, photos, documents and any Telegram media.
4. Press **Finish Upload**.
5. Send the post: either **text** or a **photo** (optionally with a caption).
6. The bot saves everything and automatically publishes the post to the channel with a
   **Download** button. Temporary files are cleared.
7. **Statistics** shows total posts, files and downloads. **Cancel Current Upload** aborts
   the current flow.

### User

1. In the channel, press **Download**.
2. If not subscribed to every required channel, the bot sends the join list with
   `Join Channel 1..N` buttons and an `I've Joined` button.
3. After joining, press **I've Joined**. If everything is fine, the files are delivered to the
   user's private chat with a progress message. Each successful delivery is counted.
4. If a channel is still missing, the bot shows `You must join all channels first.`

> Tip: users must have started the bot (pressed `/start`) for it to be able to send them files.

---

## Database

Schema is managed with Alembic:

```bash
# Apply all migrations
alembic upgrade head

# Create a new migration after editing database/models.py
alembic revision --autogenerate -m "describe change"
```

The startup `init_db()` is only a safety net and creates missing tables; use Alembic for schema
changes.

### Models

- `posts` — `id`, `message_text`, `photo_file_id`, `created_at`
- `files` — `id`, `post_id` (FK), `telegram_file_id`, `file_type`, `original_filename`
- `download_logs` — `id`, `post_id` (FK), `user_id`, `downloaded_at`

---

## Logging

Logs are printed to stdout with `LEVEL | module | message` format:

- `Admin upload: added document (total=3)` — uploads
- `Download completed: user=... post=... files=...` — downloads
- `Membership failure: user=... not in @channel` — membership failures
- `Unexpected download error: ...` / `Unhandled update error ...` — errors

Set `LOG_LEVEL=DEBUG` for more detail.

---

## Troubleshooting

| Problem                                        | Fix                                                                 |
|------------------------------------------------|---------------------------------------------------------------------|
| `BOT_TOKEN is missing`                         | Create `.env` from `.env.example` and set `BOT_TOKEN`.              |
| Admin panel does not appear for `/start`       | `ADMIN_ID` must be your numeric user id, not a username.            |
| `Failed to publish`                            | The bot is not an admin of `CHANNEL_ID` or lacks post permission.   |
| Membership checks always fail                  | The bot must be a member/admin of every `REQUIRED_CHANNELS`.        |
| Bot cannot message a user after pressing Download | The user must `/start` the bot once. The bot tells them to.       |
| Ports/files issues in Docker                   | The compose file mounts `./bot.db`; delete it to start fresh.       |

---

## License

MIT — use it freely for your own projects.
