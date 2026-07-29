# Telegram CV Builder

A Telegram bot that guides users through a short CV questionnaire, saves their progress,
shows a preview, and generates a polished A4 PDF.

## Features

- Guided, mobile-friendly CV creation
- Professional profile, skills, experience, and education sections
- Persistent per-user drafts stored as JSON
- One-tap PDF download
- `/delete` command for user-controlled data removal
- Unicode-capable PDF output when a compatible system font is available

## Run locally

1. Create a bot with Telegram's **@BotFather** and copy its token.
2. Create and activate a virtual environment:

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. Install the project:

   ```bash
   pip install -e ".[dev]"
   ```

4. Configure the bot:

   ```bash
   cp .env.example .env
   ```

   Add the BotFather token to `TELEGRAM_BOT_TOKEN` in `.env`.

5. Start polling:

   ```bash
   cv-bot
   ```

## Bot commands

- `/create` — create or replace a CV
- `/preview` — preview the saved CV
- `/pdf` — generate and download the PDF
- `/delete` — delete saved user data
- `/cancel` — cancel the current questionnaire
- `/help` — show usage help

## Data

User CV data is stored under `CV_BOT_DATA_DIR` (`./data` by default). The directory is
excluded from Git. For production, mount it on persistent encrypted storage and restrict
filesystem access to the bot process.

## Test

```bash
pytest
ruff check .
```

