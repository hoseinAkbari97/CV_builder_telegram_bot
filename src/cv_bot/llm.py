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
        enhanced = _apply_enhancement(value, original)
        return enhanced


def _prompt(cv: CV) -> str:
    language = "Persian" if cv.language == "fa" else "English"
    schema = {
        "summary": "string",
        "skills": ["string"],
        "experience_descriptions": ["string"],
    }
    explicit_skills, skill_requests = _partition_skills(cv.skills)
    cv_context = {
        "professional_title": cv.professional_title,
        "summary": cv.summary,
        "skills": explicit_skills,
        "experiences": [
            {
                "company": experience.company,
                "role": experience.role,
                "dates": experience.dates,
                "description": experience.description,
            }
            for experience in cv.experiences
        ],
        "education": [
            {
                "institution": education.institution,
                "degree": education.degree,
                "dates": education.dates,
            }
            for education in cv.education
        ],
    }
    return (
        f"Edit this CV in professional, concise {language}. Return only editable content. "
        "Improve the summary and experience descriptions with strong action verbs and "
        "ATS-friendly phrasing. Never invent employers, dates, degrees, metrics, technologies, "
        "achievements, or qualifications. Keep every explicit skill. Add skills only when they "
        "are directly supported by the title, summary, or experience. Skill requests are "
        "instructions and must never appear as skills. Return one experience description for "
        "each input experience, in the same order. "
        f"Return exactly this JSON shape: {json.dumps(schema)}\n"
        f"Explicit skills: {json.dumps(explicit_skills, ensure_ascii=False)}\n"
        f"Skill requests: {json.dumps(skill_requests, ensure_ascii=False)}\n"
        f"CV data: {json.dumps(cv_context, ensure_ascii=False)}"
    )


def _extract_json(content: str) -> str:
    start = content.find("{")
    end = content.rfind("}")
    if start == -1 or end <= start:
        raise ValueError("The model did not return a JSON object")
    return content[start : end + 1]


def _apply_enhancement(value: object, original: CV) -> CV:
    if not isinstance(value, dict):
        raise TypeError("The model response must be a JSON object")
    summary = str(value.get("summary", "")).strip()
    descriptions = value.get("experience_descriptions", [])
    generated_skills = value.get("skills", [])
    if not summary:
        raise ValueError("The model returned an empty summary")
    if not isinstance(descriptions, list) or len(descriptions) != len(original.experiences):
        raise ValueError("The model changed the experience count")
    if not isinstance(generated_skills, list):
        raise TypeError("The model returned invalid skills")

    enhanced = CV.from_dict(original.to_dict())
    enhanced.summary = summary
    enhanced.skills = _merge_skills(original.skills, generated_skills)
    for experience, description in zip(
        enhanced.experiences,
        descriptions,
        strict=True,
    ):
        polished = str(description).strip()
        if not polished:
            raise ValueError("The model returned an empty experience description")
        experience.description = polished
    return enhanced


def _merge_skills(original: list[str], generated: list[object]) -> list[str]:
    explicit, _ = _partition_skills(original)
    merged: list[str] = []
    seen: set[str] = set()
    for skill in [*explicit, *(str(item).strip() for item in generated)]:
        normalized = skill.casefold()
        if not skill or _is_skill_instruction(skill) or normalized in seen:
            continue
        seen.add(normalized)
        merged.append(skill)
    if not merged:
        raise ValueError("The model did not return factual skills")
    return merged[:12]


def _partition_skills(skills: list[str]) -> tuple[list[str], list[str]]:
    explicit: list[str] = []
    requests: list[str] = []
    for skill in skills:
        (requests if _is_skill_instruction(skill) else explicit).append(skill)
    return explicit, requests


def _is_skill_instruction(value: str) -> bool:
    normalized = " ".join(value.casefold().split())
    phrases = (
        "use ai",
        "use artificial intelligence",
        "fill other",
        "fill the rest",
        "add other",
        "add more",
        "suggest other",
        "suggest more",
        "complete this",
        "هوش مصنوعی",
        "پیشنهاد بده",
        "پیشنهاد دهید",
        "اضافه کن",
        "اضافه کنید",
        "کامل کن",
        "بقیه",
    )
    return any(phrase in normalized for phrase in phrases)
