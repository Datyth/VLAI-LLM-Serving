"""
This layer receives requests from clients, calls LLMService, and forwards the results.
"""

from typing import Any

import httpx
from fastapi import APIRouter, Depends, Request
from fastapi.responses import Response, StreamingResponse
from starlette.background import BackgroundTask

from llm_api.services.llm.service import LLMService

router = APIRouter(prefix="/v1", tags=["OpenAI"])


def get_llm_service(request: Request) -> LLMService:
    return request.app.state.llm_service


def json_response(
    response: httpx.Response,
    content: bytes,
) -> Response:
    return Response(
        content=content,
        status_code=response.status_code,
        media_type=response.headers.get("content-type", "application/json").split(
            ";", 1
        )[0],
    )


@router.get("/models")
async def models(
    service: LLMService = Depends(get_llm_service),
) -> Response:
    upstream = await service.list_model()
    return json_response(upstream, upstream.content)


@router.post("/chat/completions")
async def chat_completions(
    payload: dict[str, Any],
    service: LLMService = Depends(get_llm_service),
) -> Response:
    upstream = await service.chat_completions(payload)

    if payload.get("stream") is True and upstream.is_success:
        return StreamingResponse(
            upstream.aiter_bytes(),
            status_code=upstream.status_code,
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "X-Accel-Buffering": "no",
            },
            background=BackgroundTask(upstream.aclose),
        )

    try:
        content = await upstream.aread()
        return json_response(upstream, content)
    finally:
        await upstream.aclose()
