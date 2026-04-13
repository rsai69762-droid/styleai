import asyncio
import random
from abc import ABC, abstractmethod

import httpx
from rich.console import Console

from src.models import ScrapedProduct

console = Console()

USER_AGENTS = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.2 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:133.0) Gecko/20100101 Firefox/133.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
]


class BaseScraper(ABC):
    source_name: str
    base_url: str
    delay_range: tuple[float, float] = (1.0, 3.0)
    max_retries: int = 3

    def __init__(self, country: str = "FR", language: str = "fr"):
        self.country = country
        self.language = language
        self.client = httpx.AsyncClient(
            timeout=30.0,
            follow_redirects=True,
            headers=self._base_headers(),
        )

    def _base_headers(self) -> dict[str, str]:
        return {
            "User-Agent": random.choice(USER_AGENTS),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": f"{self.language}-{self.country},{self.language};q=0.9,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }

    async def _fetch(self, url: str) -> str | None:
        for attempt in range(self.max_retries):
            try:
                self.client.headers["User-Agent"] = random.choice(USER_AGENTS)
                response = await self.client.get(url)
                if response.status_code == 200:
                    return response.text
                if response.status_code == 429:
                    wait = (attempt + 1) * 5
                    console.print(f"[yellow]Rate limited on {url}, waiting {wait}s...[/yellow]")
                    await asyncio.sleep(wait)
                    continue
                console.print(f"[red]HTTP {response.status_code} for {url}[/red]")
                return None
            except httpx.RequestError as e:
                console.print(f"[red]Request error for {url}: {e}[/red]")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
        return None

    async def _delay(self):
        delay = random.uniform(*self.delay_range)
        await asyncio.sleep(delay)

    @abstractmethod
    async def get_category_urls(self, gender: str) -> list[str]:
        """Return list of category listing page URLs to crawl."""
        ...

    @abstractmethod
    async def parse_listing_page(self, html: str, url: str) -> list[str]:
        """Extract product URLs from a category listing page."""
        ...

    @abstractmethod
    async def parse_product_page(self, html: str, url: str) -> ScrapedProduct | None:
        """Extract product data from a product detail page."""
        ...

    async def scrape_category(self, gender: str, max_products: int = 100) -> list[ScrapedProduct]:
        """Scrape products from all categories for a given gender."""
        products: list[ScrapedProduct] = []
        category_urls = await self.get_category_urls(gender)

        for cat_url in category_urls:
            if len(products) >= max_products:
                break

            console.print(f"[blue]Fetching category: {cat_url}[/blue]")
            html = await self._fetch(cat_url)
            if not html:
                continue

            product_urls = await self.parse_listing_page(html, cat_url)
            console.print(f"  Found {len(product_urls)} products")

            for product_url in product_urls:
                if len(products) >= max_products:
                    break

                await self._delay()
                product_html = await self._fetch(product_url)
                if not product_html:
                    continue

                product = await self.parse_product_page(product_html, product_url)
                if product:
                    products.append(product)
                    console.print(f"  [green]Scraped: {product.title[:60]}[/green]")

        return products

    async def close(self):
        await self.client.aclose()
