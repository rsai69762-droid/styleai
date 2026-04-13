import json
import re
from datetime import datetime
from decimal import Decimal

from bs4 import BeautifulSoup
from rich.console import Console

from src.base_scraper import BaseScraper
from src.models import ScrapedProduct, SizeInfo

console = Console()

# Zalando FR category URLs by gender
ZALANDO_CATEGORIES = {
    "women": [
        "/femme/vetements-femme/",
        "/femme/robes/",
        "/femme/tops/",
        "/femme/pantalons-femme/",
        "/femme/jeans-femme/",
        "/femme/pulls-gilets/",
        "/femme/vestes-femme/",
        "/femme/manteaux-femme/",
        "/femme/jupes/",
        "/femme/chemisiers-tuniques/",
    ],
    "men": [
        "/homme/vetements-homme/",
        "/homme/t-shirts-polos/",
        "/homme/chemises-homme/",
        "/homme/pantalons-homme/",
        "/homme/jeans-homme/",
        "/homme/pulls-gilets-homme/",
        "/homme/vestes-homme/",
        "/homme/manteaux-homme/",
        "/homme/shorts/",
        "/homme/sweats-homme/",
    ],
}

CATEGORY_MAP = {
    "vetements-femme": ("clothing", "all"),
    "robes": ("clothing", "dresses"),
    "tops": ("clothing", "tops"),
    "pantalons-femme": ("clothing", "pants"),
    "jeans-femme": ("clothing", "jeans"),
    "pulls-gilets": ("clothing", "knitwear"),
    "vestes-femme": ("clothing", "jackets"),
    "manteaux-femme": ("clothing", "coats"),
    "jupes": ("clothing", "skirts"),
    "chemisiers-tuniques": ("clothing", "blouses"),
    "vetements-homme": ("clothing", "all"),
    "t-shirts-polos": ("clothing", "t-shirts"),
    "chemises-homme": ("clothing", "shirts"),
    "pantalons-homme": ("clothing", "pants"),
    "jeans-homme": ("clothing", "jeans"),
    "pulls-gilets-homme": ("clothing", "knitwear"),
    "vestes-homme": ("clothing", "jackets"),
    "manteaux-homme": ("clothing", "coats"),
    "shorts": ("clothing", "shorts"),
    "sweats-homme": ("clothing", "sweatshirts"),
}


class ZalandoScraper(BaseScraper):
    source_name = "zalando"
    base_url = "https://www.zalando.fr"
    delay_range = (2.0, 4.0)

    async def get_category_urls(self, gender: str) -> list[str]:
        categories = ZALANDO_CATEGORIES.get(gender, [])
        return [f"{self.base_url}{cat}" for cat in categories]

    async def parse_listing_page(self, html: str, url: str) -> list[str]:
        """Extract product URLs from Zalando category page."""
        soup = BeautifulSoup(html, "lxml")
        product_urls = []

        # Zalando product links follow pattern /nom-produit/SKU.html
        for link in soup.find_all("a", href=True):
            href = link["href"]
            # Product URLs match pattern: /brand-name-product.html or contain .html
            if re.match(r"^/[^/]+-[A-Z0-9]+\.html", href):
                full_url = f"{self.base_url}{href}" if href.startswith("/") else href
                if full_url not in product_urls:
                    product_urls.append(full_url)

        return product_urls

    async def parse_product_page(self, html: str, url: str) -> ScrapedProduct | None:
        """Extract product data from Zalando product page using JSON-LD."""
        soup = BeautifulSoup(html, "lxml")

        # Find JSON-LD structured data
        json_ld = None
        for script in soup.find_all("script", type="application/ld+json"):
            try:
                data = json.loads(script.string)
                if isinstance(data, dict) and data.get("@type") == "Product":
                    json_ld = data
                    break
                if isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict) and item.get("@type") == "Product":
                            json_ld = item
                            break
            except (json.JSONDecodeError, TypeError):
                continue

        if not json_ld:
            console.print(f"[yellow]No JSON-LD Product found for {url}[/yellow]")
            return None

        try:
            # Extract price from offers
            offers = json_ld.get("offers", {})
            if isinstance(offers, list):
                offers = offers[0] if offers else {}
            price_str = offers.get("price", offers.get("lowPrice", "0"))
            price = Decimal(str(price_str))
            currency = offers.get("priceCurrency", "EUR")

            # Extract brand
            brand_data = json_ld.get("brand", {})
            brand = brand_data.get("name", "") if isinstance(brand_data, dict) else str(brand_data)

            # Extract images
            image_data = json_ld.get("image", [])
            if isinstance(image_data, str):
                image_urls = [image_data]
            elif isinstance(image_data, list):
                image_urls = [img if isinstance(img, str) else img.get("url", "") for img in image_data]
            else:
                image_urls = []
            image_urls = [img for img in image_urls if img]

            # Extract external ID from URL (SKU)
            sku_match = re.search(r"([A-Z0-9]{2}[A-Z0-9]+-[A-Z0-9]+)\.html", url)
            external_id = json_ld.get("sku", sku_match.group(1) if sku_match else url.split("/")[-1].replace(".html", ""))

            # Determine gender from URL
            gender = "women" if "/femme/" in url or "/femme-" in url else "men" if "/homme/" in url or "/homme-" in url else "unisex"

            # Extract category from URL path
            category = "clothing"
            subcategory = None
            for cat_key, (cat, subcat) in CATEGORY_MAP.items():
                if cat_key in url:
                    category = cat
                    subcategory = subcat
                    break

            # Extract description
            description = json_ld.get("description", "")

            # Try to extract colors from page (not always in JSON-LD)
            colors = []
            color_match = json_ld.get("color", "")
            if color_match:
                colors = [color_match] if isinstance(color_match, str) else list(color_match)

            # Try to extract sizes
            sizes = []
            # Zalando sometimes has size info in offers
            if isinstance(json_ld.get("offers"), list):
                for offer in json_ld["offers"]:
                    size_val = offer.get("size", offer.get("name", ""))
                    if size_val:
                        available = offer.get("availability", "").endswith("InStock")
                        sizes.append(SizeInfo(size=str(size_val), available=available))

            # Extract material from description if present
            material = None
            material_patterns = [
                r"(\d+%\s*\w+(?:\s*,\s*\d+%\s*\w+)*)",
                r"(coton|polyester|viscose|laine|soie|lin|elasthanne|nylon|cuir)",
            ]
            if description:
                for pattern in material_patterns:
                    mat = re.search(pattern, description, re.IGNORECASE)
                    if mat:
                        material = mat.group(0)
                        break

            title = json_ld.get("name", "")
            if not title or not price or not image_urls:
                console.print(f"[yellow]Incomplete data for {url}[/yellow]")
                return None

            return ScrapedProduct(
                source="zalando",
                external_id=external_id,
                title=title,
                description=description,
                brand=brand,
                price=price,
                currency=currency,
                original_url=url,
                image_urls=image_urls[:5],
                category=category,
                subcategory=subcategory,
                gender=gender,
                sizes=sizes,
                colors=colors,
                material=material,
                country=self.country,
                language=self.language,
                scraped_at=datetime.now(),
            )

        except Exception as e:
            console.print(f"[red]Error parsing {url}: {e}[/red]")
            return None
