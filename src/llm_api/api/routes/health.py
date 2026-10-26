from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(tags = ["Health"])

class HealthResponser(BaseModel):
    status: Literal["ok"]

@router.get("/health", response_model = HealthResponser)
async def health_check() -> HealthResponser:
    return HealthResponser(status = "ok")
    