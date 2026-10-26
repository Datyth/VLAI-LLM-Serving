import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI

from llm_api.api.routes.health import router as health_router
from llm_api.api.routes.openai import router as openai_router
from llm_api.core.config import get_settings
from llm_api.services.llm.service import LLMService

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()

    timeout = httpx.Timeout(
        settings.vllm_timeout_seconds,
        connect=10.0,
    )

    async with httpx.AsyncClient(
        base_url=settings.vllm_base_url.rstrip("/") + "/",
        timeout=timeout,
        trust_env=False,
    ) as client:
        app.state.llm_service = LLMService(client)
        logger.info("LLM HTTP client initialized")
        yield

    logger.info("LLM HTTP client closed")


def create_app() -> FastAPI:
    app = FastAPI(
        title="VLAI LLM Serving",
        version="0.1.0",
        lifespan=lifespan,
    )

    app.include_router(health_router)
    app.include_router(openai_router)

    return app


app = create_app()
