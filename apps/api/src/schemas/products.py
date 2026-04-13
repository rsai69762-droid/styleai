"""Product request/response schemas."""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class ProductOut(BaseModel):
    id: uuid.UUID
    source: str
    slug: str
    title: str
    description: str | None = None
    brand: str | None = None
    price_cents: int
    currency: str = "EUR"
    original_url: str
    affiliate_url: str | None = None
    image_urls: list[str] = []
    category: str | None = None
    subcategory: str | None = None
    gender: str | None = None
    sizes: dict | list = []
    colors: list[str] = []
    material: str | None = None
    tags: list[str] = []
    language: str = "fr"
    scraped_at: datetime
    is_available: bool = True

    model_config = {"from_attributes": True}


class ProductListOut(BaseModel):
    products: list[ProductOut]
    total: int
    page: int
    page_size: int


class ProductSearchParams(BaseModel):
    q: str = Field(..., min_length=1, max_length=500)
    gender: str | None = None
    category: str | None = None
    brand: str | None = None
    min_price: int | None = Field(None, ge=0, description="Min price in cents")
    max_price: int | None = Field(None, ge=0, description="Max price in cents")
    tags: list[str] | None = None
    limit: int = Field(20, ge=1, le=100)


class ProductSearchResultOut(BaseModel):
    product: ProductOut
    score: float


class ProductSearchOut(BaseModel):
    results: list[ProductSearchResultOut]
    query: str
    total: int
