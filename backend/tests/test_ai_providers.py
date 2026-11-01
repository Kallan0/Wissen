from unittest.mock import patch

import pytest

from ai.generator import ResumeGenerator
from config import settings


class FakeResponse:
    def __init__(self, status_code=200, payload=None, text="", headers=None):
        self.status_code = status_code
        self._payload = payload or {}
        self.text = text
        self.headers = headers or {}

    def json(self):
        return self._payload


class FakeAsyncClient:
    calls = []
    response = FakeResponse()

    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return None

    async def post(self, url, **kwargs):
        self.calls.append(("POST", url, kwargs))
        return self.response

    async def get(self, url, **kwargs):
        self.calls.append(("GET", url, kwargs))
        return self.response


@pytest.fixture(autouse=True)
def reset_fake_client():
    FakeAsyncClient.calls = []
    FakeAsyncClient.response = FakeResponse()


def test_groq_requires_server_side_key(monkeypatch):
    monkeypatch.setattr(settings, "GROQ_API_KEY", "")
    with pytest.raises(RuntimeError, match="GROQ_API_KEY"):
        ResumeGenerator()._resolve_provider("groq::llama-3.1-8b-instant")


def test_groq_model_is_allow_listed(monkeypatch):
    monkeypatch.setattr(settings, "GROQ_API_KEY", "secret")
    monkeypatch.setattr(settings, "GROQ_MODELS", ("llama-3.1-8b-instant",))
    with pytest.raises(ValueError, match="allow-list"):
        ResumeGenerator()._resolve_provider("groq::unapproved-model")


def test_cloud_only_mode_never_selects_ollama(monkeypatch):
    monkeypatch.setattr(settings, "OLLAMA_ENABLED", False)
    monkeypatch.setattr(settings, "GROQ_API_KEY", "secret")
    monkeypatch.setattr(settings, "GROQ_DEFAULT_MODEL", "llama-3.1-8b-instant")
    assert ResumeGenerator()._resolve_provider(None) == ("groq", "llama-3.1-8b-instant")
    with pytest.raises(RuntimeError, match="disabled"):
        ResumeGenerator()._resolve_provider("ollama::llama3")


@pytest.mark.asyncio
async def test_groq_json_generation_uses_chat_completions(monkeypatch):
    monkeypatch.setattr(settings, "GROQ_API_KEY", "server-secret")
    monkeypatch.setattr(settings, "GROQ_BASE_URL", "https://api.groq.test/openai/v1")
    monkeypatch.setattr(settings, "GROQ_MODELS", ("llama-3.1-8b-instant",))
    FakeAsyncClient.response = FakeResponse(payload={
        "choices": [{"message": {"content": '{"status":"ok"}'}}]
    })

    with patch("ai.generator.httpx.AsyncClient", FakeAsyncClient):
        parsed, label = await ResumeGenerator()._generate_json(
            system_prompt="System facts",
            user_prompt="User task",
            model="groq::llama-3.1-8b-instant",
            temperature=0.2,
        )

    assert parsed == {"status": "ok"}
    assert label == "Groq (llama-3.1-8b-instant)"
    method, url, request = FakeAsyncClient.calls[0]
    assert method == "POST"
    assert url == "https://api.groq.test/openai/v1/chat/completions"
    assert request["headers"]["Authorization"] == "Bearer server-secret"
    assert request["json"]["response_format"] == {"type": "json_object"}
    assert request["json"]["messages"] == [
        {"role": "system", "content": "System facts"},
        {"role": "user", "content": "User task"},
    ]


@pytest.mark.asyncio
async def test_model_options_include_cloud_only_when_configured(monkeypatch):
    generator = ResumeGenerator()
    monkeypatch.setattr(generator, "get_available_models", lambda: None)

    async def local_models():
        return ["llama3:latest"]

    monkeypatch.setattr(generator, "get_available_models", local_models)
    monkeypatch.setattr(settings, "GROQ_MODELS", ("llama-3.1-8b-instant",))
    monkeypatch.setattr(settings, "AI_DEFAULT_PROVIDER", "groq")
    monkeypatch.setattr(settings, "GROQ_API_KEY", "")
    assert await generator.get_model_options() == ["llama3:latest"]

    monkeypatch.setattr(settings, "GROQ_API_KEY", "secret")
    assert await generator.get_model_options() == ["groq::llama-3.1-8b-instant", "llama3:latest"]


@pytest.mark.asyncio
async def test_query_expansion_combines_llm_and_deterministic_frontend_concepts(monkeypatch):
    generator = ResumeGenerator()

    async def fake_generate_json(**kwargs):
        return {"concepts": ["Frontend Development", "Next.js", "next.js"]}, "Test Provider"

    monkeypatch.setattr(generator, "_generate_json", fake_generate_json)
    concepts = await generator.expand_job_query(
        "Build responsive frontend interfaces",
        "Frontend Developer Intern",
        "groq::test",
    )

    assert concepts.count("Next.js") == 1
    assert "React" in concepts
    assert "Tailwind CSS" in concepts
    assert "UI/UX" in concepts
