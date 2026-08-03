import asyncio
import json

import httpx

from cv_bot.llm import CVEnhancer, Provider
from cv_bot.models import CV


def _provider(name: str) -> Provider:
    return Provider(
        name=name,
        url=f"https://{name}.example/chat",
        api_key="secret",
        models=("free-model",),
        headers={},
    )


def test_enhancer_uses_next_provider(monkeypatch) -> None:
    original = CV(
        full_name="Ada Lovelace",
        professional_title="Engineer",
        email="ada@example.com",
        summary="I build software.",
        skills=["Python"],
    )
    enhanced_payload = original.to_dict()
    enhanced_payload["summary"] = "Builds reliable software."

    async def fake_post(self, url, **kwargs):
        request = httpx.Request("POST", url)
        if "first" in url:
            return httpx.Response(503, request=request)
        body = {"choices": [{"message": {"content": json.dumps(enhanced_payload)}}]}
        return httpx.Response(200, request=request, json=body)

    monkeypatch.setattr(httpx.AsyncClient, "post", fake_post)
    result = asyncio.run(
        CVEnhancer([_provider("first"), _provider("second")]).enhance(original)
    )

    assert result.summary == "Builds reliable software."
    assert result.content_source == "second:free-model"


def test_enhancer_returns_static_cv_when_all_providers_fail(monkeypatch) -> None:
    original = CV(
        full_name="Ada Lovelace",
        professional_title="Engineer",
        email="ada@example.com",
        summary="I build software.",
    )

    async def fake_post(self, url, **kwargs):
        request = httpx.Request("POST", url)
        return httpx.Response(503, request=request)

    monkeypatch.setattr(httpx.AsyncClient, "post", fake_post)
    result = asyncio.run(CVEnhancer([_provider("offline")]).enhance(original))

    assert result is original
    assert result.content_source == "static"
