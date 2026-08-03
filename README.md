# Telegram CV Builder

A bilingual Telegram bot that guides users through a CV questionnaire, optionally
polishes the content with free-tier LLM providers, and generates a selected A4 PDF design.

## Features

- Guided, mobile-friendly CV creation
- English and Persian user flows and PDF output
- Explicit, persistent bot-language selection
- Hybrid AI fallback: Groq models → OpenRouter free models → Cloudflare Workers AI
- Automatic static fallback when no AI provider succeeds
- Nine professional templates with Telegram image previews
- Optional profile-photo upload and PDF placement
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

   Add the BotFather token to `TELEGRAM_BOT_TOKEN` in `.env`. Then configure one or
   more optional AI providers:

   - `GROQ_API_KEY`: tries every entry in `GROQ_MODELS` in order.
   - `OPENROUTER_API_KEY`: uses `openrouter/free` by default, or a comma-separated
     list of specific free model IDs.
   - `CLOUDFLARE_API_TOKEN` and `CLOUDFLARE_ACCOUNT_ID`: tries every entry in
     `CLOUDFLARE_MODELS`.

   Provider and model failures are isolated. The bot continues through the chain and
   saves the user's original content if every request fails.

5. Start polling:

   ```bash
   cv-bot
   ```

## Bot commands

- `/create` — create or replace a CV
- `/language` — change the bot language
- `/templates` — preview and select a PDF template
- `/preview` — preview the saved CV
- `/pdf` — generate and download the PDF
- `/delete` — delete saved user data
- `/cancel` — cancel the current questionnaire
- `/help` — show usage help

## Data

User CV data is stored under `CV_BOT_DATA_DIR` (`./data` by default). The directory is
excluded from Git. For production, mount it on persistent encrypted storage and restrict
filesystem access to the bot process.

The bot sends CV content to any configured AI provider. Update your privacy policy and
obtain user consent before using third-party APIs in production. API keys remain server-side.

## Test

```bash
pytest
ruff check .
```
