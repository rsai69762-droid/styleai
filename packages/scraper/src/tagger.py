"""Auto-tagger: generates tags from product title, subcategory, brand, and colors."""

import re

# Fit / cut tags — order matters: longer patterns first to avoid partial matches
FIT_PATTERNS: list[tuple[str, str]] = [
    (r"\bwide[- ]?leg\b", "wide-leg"),
    (r"\bboot[- ]?cut\b", "bootcut"),
    (r"\bhigh[- ]?waist\b", "high-waist"),
    (r"\bmid[- ]?waist\b", "mid-waist"),
    (r"\bsuper\s*skinny\b", "super-skinny"),
    (r"\bskinny\b", "skinny"),
    (r"\bslim\b", "slim"),
    (r"\bstraight\b", "straight"),
    (r"\bflare[d]?\b", "flare"),
    (r"\bmom\b", "mom"),
    (r"\bboyfriend\b", "boyfriend"),
    (r"\bbaggy\b", "baggy"),
    (r"\bballoon\b", "balloon"),
    (r"\boversize[d]?\b", "oversize"),
    (r"\brelax(?:ed)?\b", "relaxed"),
    (r"\btaper(?:ed)?\b", "tapered"),
    (r"\bregular\b", "regular"),
    (r"\bcrop(?:ped)?\b", "cropped"),
    (r"\bpetite\b", "petite"),
    (r"\blarge\b", "wide-leg"),
    # Length (FR)
    (r"\bcourt[e]?\b", "courte"),
    (r"\bmi-long(?:ue)?\b", "mi-longue"),
    (r"\blong(?:ue)?\b", "longue"),
    # Neckline / details (FR)
    (r"\bcol[- ]?v\b", "col-v"),
    (r"\bencolure[- ]?carr[ée]e\b", "encolure-carree"),
    (r"\bbretelles?\b", "bretelles"),
    (r"\bsans[- ]?manches?\b", "sans-manches"),
]

# Style tags
STYLE_PATTERNS: list[tuple[str, str]] = [
    (r"\bripped\b", "ripped"),
    (r"\bvintage\b", "vintage"),
    (r"\bdistressed\b", "distressed"),
    (r"\bwashed\b", "washed"),
    (r"\bdelav[ée]\b", "washed"),
    (r"\braw\b", "raw-denim"),
    (r"\bpush[- ]?up\b", "push-up"),
    (r"\bshaping\b", "shaping"),
    (r"\bstretch\b", "stretch"),
    (r"\bflexi\b", "stretch"),
    (r"\b7/8\b", "7/8"),
    (r"\bbroderie\b", "broderie"),
    (r"\bdentelle\b", "dentelle"),
    (r"\bimprim[ée]\b", "imprime"),
    (r"\bfleur[si]?\b", "fleuri"),
    (r"\bfleuri\b", "fleuri"),
    (r"\bpois\b", "a-pois"),
    (r"\bcarreaux\b", "a-carreaux"),
    (r"\bvichy\b", "vichy"),
    (r"\brayure[s]?\b", "rayures"),
    (r"\bray[ée][s]?\b", "rayures"),
    (r"\bfronc[ée]\b", "fronce"),
    (r"\bvolant[s]?\b", "volants"),
    (r"\bnoué\b", "noue"),
    (r"\bn[œo]ud\b", "noue"),
    (r"\bdos[- ]?nu\b", "dos-nu"),
    (r"\bportefeuille\b", "portefeuille"),
    (r"\bbabydoll\b", "babydoll"),
    (r"\btrap[èe]ze\b", "trapeze"),
    (r"\bmoulant[e]?\b", "moulante"),
    (r"\bfluide\b", "fluide"),
    (r"\bplage\b", "plage"),
    (r"\bd['']?[ée]t[ée]\b", "ete"),
    (r"\blin\b", "lin"),
    (r"\bcoton\b", "coton"),
    (r"\bpopeline\b", "popeline"),
    (r"\bjean\b(?!s)", "denim"),
    (r"\bdenim\b", "denim"),
    (r"\bsatin\b", "satin"),
    (r"\bsoie\b", "soie"),
]

# Garment type from subcategory or title
GARMENT_PATTERNS: list[tuple[str, str]] = [
    (r"\bjeans?\b", "jeans"),
    (r"\bshort\b", "short"),
    (r"\brobe\b", "robe"),
    (r"\bdress\b", "robe"),
    (r"\bkleid\b", "robe"),
    (r"\bt[- ]?shirt\b", "t-shirt"),
    (r"\btop\b", "top"),
    (r"\bblouse\b", "blouse"),
    (r"\bchemis(?:e|ier)\b", "chemise"),
    (r"\btunique\b", "tunique"),
    (r"\bpull\b", "pull"),
    (r"\bsweater\b", "pull"),
    (r"\bgilet\b", "gilet"),
    (r"\bcardigan\b", "cardigan"),
    (r"\bveste\b", "veste"),
    (r"\bjacket\b", "veste"),
    (r"\bmanteau\b", "manteau"),
    (r"\bcoat\b", "manteau"),
    (r"\bparka\b", "parka"),
    (r"\bblazer\b", "blazer"),
    (r"\bpantalon\b", "pantalon"),
    (r"\btrouser\b", "pantalon"),
    (r"\bjupe\b", "jupe"),
    (r"\bskirt\b", "jupe"),
    (r"\bcombinaison\b", "combinaison"),
    (r"\bjumpsuit\b", "combinaison"),
    (r"\bsweat\b", "sweat"),
    (r"\bhoodie\b", "hoodie"),
    (r"\bpolo\b", "polo"),
    (r"\bjogging\b", "jogging"),
    (r"\blegging\b", "legging"),
    (r"\bbody\b", "body"),
    (r"\bcrop[- ]?top\b", "crop-top"),
    (r"\bdebardeur\b", "debardeur"),
    (r"\btank\b", "debardeur"),
    # Shoes / Chaussures
    (r"\bbaskets?\b", "baskets"),
    (r"\btrainers?\b", "baskets"),
    (r"\bsneakers?\b", "baskets"),
    (r"\bsandal(?:es|s)?\b", "sandales"),
    (r"\bspartiat(?:es|e)\b", "sandales"),
    (r"\btongs?\b", "tongs"),
    (r"\bescarpins?\b", "escarpins"),
    (r"\bsabots?\b", "sabots"),
    (r"\bmules?\b", "mules"),
    (r"\bmocassins?\b", "mocassins"),
    (r"\bballerines?\b", "ballerines"),
    (r"\bbottes?\b", "bottes"),
    (r"\bbottines?\b", "bottines"),
    (r"\bchaussures?\b", "chaussures"),
    (r"\bderbi(?:es|s|)\b", "derbies"),
    (r"\bloafers?\b", "mocassins"),
    (r"\bchaussures?\s+de\s+skate\b", "baskets"),
    (r"\bchaussures?\s+bateau\b", "chaussures-bateau"),
    (r"\bchaussures?\s+de\s+running\b", "running"),
    (r"\bchaussures?\s+fitness\b", "fitness"),
    # Accessories / Accessoires
    (r"\bsac\s+[àa]\s+main\b", "sac-a-main"),
    (r"\bsac\s+bandouli[èe]re\b", "sac-bandouliere"),
    (r"\bsac\s+[àa]\s+dos\b", "sac-a-dos"),
    (r"\bcabas\b", "cabas"),
    (r"\bpochette\b", "pochette"),
    (r"\bportefeuille\b", "portefeuille"),
    (r"\bcasquette\b", "casquette"),
    (r"\bbonnet\b", "bonnet"),
    (r"\bchapeau\b", "chapeau"),
    (r"\bceinture\b", "ceinture"),
    (r"\blunettes?\b", "lunettes"),
    (r"\bboucles?\s+d['']oreilles?\b", "bijoux"),
    (r"\bcollier\b", "bijoux"),
    (r"\bbracelet\b", "bijoux"),
    (r"\bbague\b", "bijoux"),
    (r"\b[ée]charpe\b", "echarpe"),
    (r"\bfoulard\b", "foulard"),
]

# Color normalization: raw color words → normalized tag
COLOR_MAP: dict[str, str] = {
    # Blues
    "blue": "bleu", "bleu": "bleu", "blu": "bleu", "navy": "bleu-marine",
    "marine": "bleu-marine", "indigo": "indigo", "denim": "bleu",
    "rinse": "bleu-fonce", "royal": "bleu",
    # Blacks
    "black": "noir", "noir": "noir", "schwarz": "noir",
    # Whites
    "white": "blanc", "blanc": "blanc", "weiß": "blanc", "weiss": "blanc",
    "bianco": "blanc", "ecru": "ecru", "cream": "creme", "ivory": "ivoire",
    # Greys
    "grey": "gris", "gray": "gris", "gris": "gris",
    # Browns
    "brown": "marron", "marron": "marron", "camel": "camel",
    "tan": "camel", "beige": "beige", "khaki": "kaki", "kaki": "kaki",
    # Reds
    "red": "rouge", "rouge": "rouge", "bordeaux": "bordeaux",
    "burgundy": "bordeaux", "coral": "corail",
    # Pinks
    "pink": "rose", "rose": "rose", "fuchsia": "fuchsia",
    # Greens
    "green": "vert", "vert": "vert", "olive": "olive", "kaki": "kaki",
    # Yellows / Oranges
    "yellow": "jaune", "jaune": "jaune", "orange": "orange",
    "mustard": "moutarde",
    # Purples
    "purple": "violet", "violet": "violet", "lilac": "lilas",
    "lavender": "lavande",
    # French color names (from ASOS FR titles)
    "rouge": "rouge", "rouille": "rouille", "brique": "rouille",
    "chocolat": "marron", "marron": "marron", "cendre": "marron",
    "olive": "olive", "sauge": "vert", "vert": "vert",
    "citron": "jaune", "jaune": "jaune",
    "orange": "orange",
    "marine": "bleu-marine", "cobalt": "bleu",
    "pastel": "pastel",
    "creme": "creme", "crème": "creme", "ecru": "ecru", "écru": "ecru",
    "noir": "noir",
    "blanc": "blanc",
}

# Shade modifiers to strip when normalizing colors
SHADE_WORDS = {"light", "dark", "mottled", "medium", "pale", "bright", "deep",
               "double", "stone", "snow", "used", "moon", "blue-black"}

# Brand tiers for style tagging
HIGH_STREET_BRANDS = {
    "bershka", "pull&bear", "stradivarius", "zara", "h&m", "primark",
    "new look", "boohoo", "shein", "calliope", "cache cache", "kiabi",
    "pimkie", "jennyfer", "mango", "asos design", "asos", "collusion",
    "reclaimed vintage", "monki", "weekday", "noisy may", "jdy",
    "asos design curve", "asos design tall", "asos design petite",
    "miss selfridge", "topshop", "wednesday's girl", "only", "only tall",
    "vero moda", "pieces", "vila", "jjxx", "jdy",
}
PREMIUM_BRANDS = {
    "levi's®", "levi's", "levis", "tommy hilfiger", "calvin klein",
    "guess", "diesel", "g-star", "replay", "pepe jeans", "scotch & soda",
    "boss", "lacoste", "ralph lauren", "gant", "abercrombie & fitch",
}


def generate_tags(product: dict) -> list[str]:
    """Generate a list of tags from product fields."""
    tags: set[str] = set()

    title = product.get("title", "").lower()
    subcategory = (product.get("subcategory") or "").lower()
    brand = (product.get("brand") or "").lower()
    colors = product.get("colors") or []
    search_text = f"{title} {subcategory}"

    # 1. Fit / cut
    for pattern, tag in FIT_PATTERNS:
        if re.search(pattern, search_text, re.IGNORECASE):
            tags.add(tag)

    # 2. Style
    for pattern, tag in STYLE_PATTERNS:
        if re.search(pattern, search_text, re.IGNORECASE):
            tags.add(tag)

    # 3. Garment type
    for pattern, tag in GARMENT_PATTERNS:
        if re.search(pattern, search_text, re.IGNORECASE):
            tags.add(tag)
            break  # one garment type is enough

    # 4. Colors — from title (after last " - ") and from colors field
    color_sources: list[str] = list(colors)
    # Title typically ends with "- color description"
    dash_parts = product.get("title", "").split(" - ")
    if len(dash_parts) >= 2:
        color_sources.append(dash_parts[-1])

    for color_text in color_sources:
        for word in color_text.lower().split():
            word = word.strip(".,;:!?()[]")
            if word in COLOR_MAP:
                tags.add(COLOR_MAP[word])
            elif word in SHADE_WORDS:
                continue

    # Infer "dark" or "light" shade if present
    title_lower = title
    if "dark" in title_lower and any(t in tags for t in ("bleu", "gris")):
        tags.discard("bleu")
        tags.discard("gris")
        if "bleu" in {COLOR_MAP.get(w) for w in title_lower.split()}:
            tags.add("bleu-fonce")
        elif "gris" in {COLOR_MAP.get(w) for w in title_lower.split()}:
            tags.add("gris-fonce")
    if "light" in title_lower and "bleu" in tags:
        tags.discard("bleu")
        tags.add("bleu-clair")

    # 5. Brand tier
    if brand in HIGH_STREET_BRANDS:
        tags.add("high-street")
    elif brand in PREMIUM_BRANDS:
        tags.add("premium")

    # 6. Price range
    price = float(product.get("price", 0))
    if price > 0:
        if price < 30:
            tags.add("budget")
        elif price < 60:
            tags.add("mid-range")
        elif price < 100:
            tags.add("mid-premium")
        else:
            tags.add("premium-price")

    return sorted(tags)


def tag_products(products: list[dict]) -> list[dict]:
    """Add tags to a list of product dicts. Mutates in place and returns."""
    for product in products:
        product["tags"] = generate_tags(product)
    return products
