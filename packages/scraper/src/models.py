from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, HttpUrl


class SizeInfo(BaseModel):
    size: str
    available: bool = True


class ScrapedProduct(BaseModel):
    source: Literal["zalando", "asos", "zara", "hm"]
    external_id: str
    title: str
    description: str | None = None
    brand: str
    price: Decimal
    currency: str = "EUR"
    original_url: str
    image_urls: list[str]
    category: str
    subcategory: str | None = None
    gender: Literal["men", "women", "unisex"]
    sizes: list[SizeInfo] = []
    colors: list[str] = []
    tags: list[str] = []
    material: str | None = None
    country: str = "FR"
    language: str = "fr"
    scraped_at: datetime = datetime.now()

    @property
    def price_cents(self) -> int:
        return int(self.price * 100)
