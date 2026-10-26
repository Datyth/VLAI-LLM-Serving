"""
Why use httpx.AsyncClient?
It supports asynchronous communication.
It can reuse HTTP connections across requests.
It supports streaming without loading the entire generated response into memory.
It lets FastAPI return useful errors if vLLM is unreachable.
"""

import logging
from typing import Any

import httpx
from fastapi import HTTPException

logger = logging.getLogger(__name__)


class LLMService:
    def __init__(self, client: httpx.AsyncClient):
        self.client = client

    async def list_model(self) -> httpx.Response:
        return await self._send("GET", "/v1/models")

    async def chat_completions(
        self,
        payload: dict[str, Any],
    ) -> httpx.Response:
        return await self._send(
            "POST",
            "/v1/chat/completions",
            payload=payload,
            stream=payload.get("stream") is True,
        )

    async def _send(
        self,
        method: str,
        path: str,
        payload: dict[str, Any] | None = None,
        stream: bool = False,
    ) -> httpx.Response:
        request = self.client.build_request(method, path, json=payload)

        try:
            return await self.client.send(request, stream=stream)

        except httpx.TimeoutException as exc:
            logger.warning(
                "vLLM request timed out: %s %s",
                method,
                path,
            )
            raise HTTPException(
                status_code=504,
                detail="Inference server timed out",
            ) from exc

        except httpx.RequestError as exc:
            logger.error(
                "vLLM connection failed: %s %s: %s",
                method,
                path,
                type(exc).__name__,
            )
            raise HTTPException(
                status_code=502,
                detail="Inference server unavailable",
            ) from exc
