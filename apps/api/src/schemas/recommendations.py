"""Recommendation request/response schemas."""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from src.schemas.products import ProductOut


class RecommendationGenerateIn(BaseModel):
    occasion: str | None = Field(None, description="Ex: travail, soiree, casual, plage")
    mood: str | None = Field(None, description="Ex: classique, tendance, decontracte")


class RecommendationItemOut(BaseModel):
    id: uuid.UUID
    product: ProductOut
    score: float
    reason: str | None = None
    agent_run_id: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class RecommendationGenerateOut(BaseModel):
    agent_run_id: str
    recommendations: list[RecommendationItemOut]
    context: dict = {}


class RecommendationFeedbackIn(BaseModel):
    is_dismissed: bool = False
