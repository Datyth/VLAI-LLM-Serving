import asyncio
import json
from collections.abc import Callable

import httpx
from fastapi.testclient import TestClient

from llm_api.api.routes.openai import get_llm_service
from llm_api.main import app
from llm_api.services.llm.service import LLMService


def make_request(
    handler: Callable[[httpx.Request], httpx.Response],
    payload: dict,
) -> httpx.Response:
    client = httpx.AsyncClient(
        base_url="http://mock-vllm",
        transport=httpx.MockTransport(handler),
    )

    app.dependency_overrides[get_llm_service] = lambda: LLMService(client)

    try:
        with TestClient(app) as test_client:
            return test_client.post(
                "/v1/chat/completions",
                json=payload,
            )
    finally:
        app.dependency_overrides.clear()
        asyncio.run(client.aclose())


def test_chat_completion() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/v1/chat/completions"
        assert json.loads(request.content)["model"] == "qwen3.5-9b"

        return httpx.Response(
            200,
            json={
                "choices": [
                    {
                        "message": {"content": "Hello!"},
                        "finish_reason": "stop",
                    }
                ]
            },
        )

    response = make_request(
        handler,
        {
            "model": "qwen3.5-9b",
            "messages": [{"role": "user", "content": "Hello"}],
        },
    )

    assert response.status_code == 200
    assert response.json()["choices"][0]["message"]["content"] == "Hello!"


def test_streaming_tool_call() -> None:
    events = (
        'data: {"choices":[{"delta":{"tool_calls":'
        '[{"index":0,"function":{"name":"add_numbers",'
        '"arguments":"{\\"a\\":12,\\"b\\":30}"}}]}}]}\n\n'
        "data: [DONE]\n\n"
    )

    def handler(request: httpx.Request) -> httpx.Response:
        assert json.loads(request.content)["stream"] is True

        return httpx.Response(
            200,
            headers={"content-type": "text/event-stream"},
            content=events.encode(),
        )

    response = make_request(
        handler,
        {
            "model": "qwen3.5-9b",
            "messages": [{"role": "user", "content": "Add 12 and 30"}],
            "stream": True,
        },
    )

    assert response.status_code == 200
    assert "tool_calls" in response.text
    assert "data: [DONE]" in response.text
