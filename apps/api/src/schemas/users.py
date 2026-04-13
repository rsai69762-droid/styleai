"""User request/response schemas."""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class UserOut(BaseModel):
    id: uuid.UUID
    email: str | None = None
    display_name: str | None = None
    avatar_url: str | None = None
    locale: str = "en"
    country: str | None = None

    model_config = {"from_attributes": True}


class UserProfileOut(BaseModel):
    gender: str | None = None
    age_range: str | None = None
    body_type: str | None = None
    height_cm: int | None = None
    weight_kg: int | None = None
    preferred_sizes: dict = {}
    style_tags: list[str] = []
    favorite_brands: list[str] = []
    favorite_colors: list[str] = []
    budget_min_cents: int | None = None
    budget_max_cents: int | None = None
    currency: str = "EUR"
    onboarding_completed: bool = False

    model_config = {"from_attributes": True}


class UserProfileUpdate(BaseModel):
    gender: str | None = None
    age_range: str | None = None
    body_type: str | None = None
    height_cm: int | None = Field(None, ge=100, le=250)
    weight_kg: int | None = Field(None, ge=30, le=300)
    preferred_sizes: dict | None = None
    style_tags: list[str] | None = None
    favorite_brands: list[str] | None = None
    favorite_colors: list[str] | None = None
    budget_min_cents: int | None = Field(None, ge=0)
    budget_max_cents: int | None = Field(None, ge=0)
    currency: str | None = None


class OnboardingIn(BaseModel):
    gender: str
    age_range: str
    style_tags: list[str] = Field(min_length=1)
    favorite_colors: list[str] = []
    budget_min_cents: int | None = None
    budget_max_cents: int | None = None
    preferred_sizes: dict = {}
