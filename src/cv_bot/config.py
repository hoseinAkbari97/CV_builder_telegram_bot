import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


@dataclass(frozen=True, slots=True)
class Settings:
    telegram_bot_token: str
    data_dir: Path
    groq_api_key: str = ""
    groq_models: tuple[str, ...] = ()
    openrouter_api_key: str = ""
    openrouter_models: tuple[str, ...] = ()
    cloudflare_api_token: str = ""
    cloudflare_account_id: str = ""
    cloudflare_models: tuple[str, ...] = ()
    llm_timeout_seconds: float = 25.0


def _csv(name: str, default: str) -> tuple[str, ...]:
    return tuple(
        value.strip()
        for value in os.getenv(name, default).split(",")
        if value.strip()
    )


def load_settings() -> Settings:
    load_dotenv()
    token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    if not token:
        raise RuntimeError(
            "TELEGRAM_BOT_TOKEN is missing. Copy .env.example to .env and add your token."
        )

    data_dir = Path(os.getenv("CV_BOT_DATA_DIR", "./data")).expanduser().resolve()
    data_dir.mkdir(parents=True, exist_ok=True)
    return Settings(
        telegram_bot_token=token,
        data_dir=data_dir,
        groq_api_key=os.getenv("GROQ_API_KEY", "").strip(),
        groq_models=_csv(
            "GROQ_MODELS",
            "qwen/qwen3-32b,llama-3.3-70b-versatile,mistral-saba-24b,gemma2-9b-it",
        ),
        openrouter_api_key=os.getenv("OPENROUTER_API_KEY", "").strip(),
        openrouter_models=_csv("OPENROUTER_MODELS", "openrouter/free"),
        cloudflare_api_token=os.getenv("CLOUDFLARE_API_TOKEN", "").strip(),
        cloudflare_account_id=os.getenv("CLOUDFLARE_ACCOUNT_ID", "").strip(),
        cloudflare_models=_csv(
            "CLOUDFLARE_MODELS",
            "@cf/meta/llama-3.1-8b-instruct",
        ),
        llm_timeout_seconds=float(os.getenv("LLM_TIMEOUT_SECONDS", "25")),
    )
