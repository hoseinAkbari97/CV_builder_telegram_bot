import json
import logging
from dataclasses import dataclass

import httpx

from cv_bot.config import Settings
from cv_bot.models import CV

LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class Provider:
    name: str
    url: str
    api_key: str
    models: tuple[str, ...]
    headers: dict[str, str]


class CVEnhancer:
    def __init__(self, providers: list[Provider], timeout_seconds: float = 25.0) -> None:
        self._providers = providers
        self._timeout = timeout_seconds

    @classmethod
    def from_settings(cls, settings: Settings) -> "CVEnhancer":
        providers: list[Provider] = []
        if settings.groq_api_key:
            providers.append(
                Provider(
                    name="groq",
                    url="https://api.groq.com/openai/v1/chat/completions",
                    api_key=settings.groq_api_key,
                    models=settings.groq_models,
                    headers={},
                )
            )
        if settings.openrouter_api_key:
            providers.append(
                Provider(
                    name="openrouter",
                    url="https://openrouter.ai/api/v1/chat/completions",
                    api_key=settings.openrouter_api_key,
                    models=settings.openrouter_models,
                    headers={
                        "HTTP-Referer": "https://github.com/cv-builder",
                        "X-Title": "Telegram CV Builder",
                    },
                )
            )
        if settings.cloudflare_api_token and settings.cloudflare_account_id:
            providers.append(
                Provider(
                    name="cloudflare",
                    url=(
                        "https://api.cloudflare.com/client/v4/accounts/"
                        f"{settings.cloudflare_account_id}/ai/v1/chat/completions"
                    ),
                    api_key=settings.cloudflare_api_token,
                    models=settings.cloudflare_models,
                    headers={},
                )
            )
        return cls(providers, settings.llm_timeout_seconds)

    async def enhance(self, cv: CV) -> CV:
        if not self._providers:
            return cv
        prompt = _prompt(cv)
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            for provider in self._providers:
                for model in provider.models:
                    try:
                        result = await self._request(client, provider, model, prompt, cv)
                        result.language = cv.language
                        result.template = cv.template
                        result.content_source = f"{provider.name}:{model}"
                        return result
                    except (httpx.HTTPError, KeyError, TypeError, ValueError, json.JSONDecodeError):
                        LOGGER.warning(
                            "CV enhancement failed via %s/%s",
                            provider.name,
                            model,
                            exc_info=True,
                        )
        return cv

    async def _request(
        self,
        client: httpx.AsyncClient,
        provider: Provider,
        model: str,
        prompt: str,
        original: CV,
    ) -> CV:
        response = await client.post(
            provider.url,
            headers={
                "Authorization": f"Bearer {provider.api_key}",
                "Content-Type": "application/json",
                **provider.headers,
            },
            json={
                "model": model,
                "temperature": 0.25,
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "You are an expert resume editor. Return only valid JSON, "
                            "without markdown fences."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
            },
        )
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]
        value = json.loads(_extract_json(content))
        enhanced = CV.from_dict(value)
        _validate_facts(enhanced, original=original)
        return enhanced


def _prompt(cv: CV) -> str:
    language = "Persian" if cv.language == "fa" else "English"
    schema = {
        "full_name": "string",
        "professional_title": "string",
        "email": "string",
        "phone": "string",
        "location": "string",
        "linkedin": "string",
        "summary": "string",
        "skills": ["string"],
        "experiences": [
            {
                "company": "string",
                "role": "string",
                "dates": "string",
                "description": "string",
            }
        ],
        "education": [{"institution": "string", "degree": "string", "dates": "string"}],
    }
    return (
        f"Rewrite this CV in professional, concise {language}. Improve the summary and "
        "experience descriptions with strong action verbs and ATS-friendly phrasing. "
        "Never invent employers, dates, degrees, metrics, technologies, or achievements. "
        "Keep names, contact details, institutions, roles, dates, and list lengths unchanged. "
        f"Return exactly this JSON shape: {json.dumps(schema)}\n"
        f"CV data: {json.dumps(cv.to_dict(), ensure_ascii=False)}"
    )


def _extract_json(content: str) -> str:
    start = content.find("{")
    end = content.rfind("}")
    if start == -1 or end <= start:
        raise ValueError("The model did not return a JSON object")
    return content[start : end + 1]


def _validate_facts(enhanced: CV, original: CV) -> None:
    protected = (
        "full_name",
        "email",
        "phone",
        "location",
        "linkedin",
        "professional_title",
    )
    if any(getattr(enhanced, field) != getattr(original, field) for field in protected):
        raise ValueError("The model changed protected personal facts")
    if len(enhanced.experiences) != len(original.experiences):
        raise ValueError("The model changed the experience count")
    if len(enhanced.education) != len(original.education):
        raise ValueError("The model changed the education count")
    if enhanced.skills != original.skills:
        raise ValueError("The model changed protected skills")
    for new, old in zip(enhanced.experiences, original.experiences, strict=True):
        if (new.company, new.role, new.dates) != (old.company, old.role, old.dates):
            raise ValueError("The model changed protected experience facts")
    for new, old in zip(enhanced.education, original.education, strict=True):
        if (new.institution, new.degree, new.dates) != (
            old.institution,
            old.degree,
            old.dates,
        ):
            raise ValueError("The model changed protected education facts")
