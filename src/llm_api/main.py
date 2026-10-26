import logging

from fastapi import FastAPI

from llm_api.api.routes.health import router as health_router

logger = logging.getLogger(__name__)

def create_app() -> FastAPI:
    app = FastAPI(
        title = "VLAI LLM Serving",
        version = "0.1.0"
    )

    app.include_router(health_router)
    logger.info("FastAPI application initialized")
    return app

app = create_app()
