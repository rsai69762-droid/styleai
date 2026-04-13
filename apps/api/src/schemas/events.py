"""Event tracking schemas."""

import uuid

from pydantic import BaseModel, Field


class EventIn(BaseModel):
    event_type: str = Field(..., pattern=r"^(view|click|wishlist_add|wishlist_remove|click_through|search|recommendation_view)$")
    product_id: uuid.UUID | None = None
    metadata: dict = {}
    duration_ms: int | None = Field(None, ge=0)


class EventBatchIn(BaseModel):
    session_id: uuid.UUID
    events: list[EventIn] = Field(..., min_length=1, max_length=100)
