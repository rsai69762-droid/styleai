// === StylAI - ZARA BULK Product Extractor ===
// 1. Ouvre une page listing/recherche Zara
//    ex: https://www.zara.com/fr/fr/search?searchTerm=robe%20été&section=WOMAN
//    ou: https://www.zara.com/fr/fr/femme-robes-l1066.html
// 2. SCROLL JUSQU'EN BAS pour charger tous les produits
// 3. Ouvre la console (F12 > Console)
// 4. Colle ce script et appuie sur Entree
// 5. Le JSON est telecharge automatiquement

(function() {
  const products = [];
  const seen = new Set();

  const url = window.location.href;
  const pathname = window.location.pathname;
  const searchParams = new URLSearchParams(window.location.search);

  // Gender detection from URL
  let gender = 'women';
  const section = (searchParams.get('section') || '').toLowerCase();
  if (section === 'man' || pathname.includes('/homme')) {
    gender = 'men';
  } else if (section === 'woman' || pathname.includes('/femme')) {
    gender = 'women';
  }

  // Subcategory from search term or URL path
  let subcategory = '';
  const searchTerm = searchParams.get('searchTerm');
  if (searchTerm) {
    subcategory = searchTerm.trim();
  } else {
    // Category pages: /fr/fr/femme-robes-l1066.html -> "robes"
    const pathMatch = pathname.match(/femme-(\w+)|homme-(\w+)/);
    if (pathMatch) {
      subcategory = (pathMatch[1] || pathMatch[2] || '').replace(/-/g, ' ');
    }
  }

  // Zara uses <li class="product-grid-product" data-productid="...">
  const items = document.querySelectorAll('li.product-grid-product[data-productid]');
  console.log(`Found ${items.length} product elements`);

  for (const item of items) {
    try {
      const externalId = item.getAttribute('data-productid');
      if (!externalId || seen.has(externalId)) continue;
      seen.add(externalId);

      // Product link
      const link = item.querySelector('a.product-link[href]');
      if (!link) continue;
      const href = link.getAttribute('href');
      const productUrl = href.startsWith('http') ? href.split('?')[0] : 'https://www.zara.com' + href.split('?')[0];

      // Title from <h3> inside the product name link
      const titleEl = item.querySelector('.product-grid-product-info__name h3');
      const title = titleEl ? titleEl.textContent.trim() : '';
      if (!title) continue;

      // Price: "35,95 EUR" from span.money-amount__main
      let price = 0;
      let originalPrice = 0;

      // Check for sale prices (old + current)
      const oldPriceEl = item.querySelector('.price-old .money-amount__main');
      const currentPriceEl = item.querySelector('.price-current .money-amount__main');

      if (currentPriceEl) {
        const priceText = currentPriceEl.textContent.trim();
        price = parseFloat(priceText.replace(/[^\d,]/g, '').replace(',', '.'));
      }
      if (oldPriceEl) {
        const oldText = oldPriceEl.textContent.trim();
        originalPrice = parseFloat(oldText.replace(/[^\d,]/g, '').replace(',', '.'));
      }

      // Fallback: any money-amount__main
      if (price === 0) {
        const anyPrice = item.querySelector('.money-amount__main');
        if (anyPrice) {
          price = parseFloat(anyPrice.textContent.trim().replace(/[^\d,]/g, '').replace(',', '.'));
        }
      }

      if (price === 0) {
        console.warn('Skipping product without price:', title);
        continue;
      }

      // Images: get src from media-image__image, upgrade resolution
      const images = [];
      const imgEls = item.querySelectorAll('img.media-image__image[src*="static.zara.net"]');
      for (const img of imgEls) {
        let src = img.getAttribute('src');
        if (src) {
          // Upgrade image width: w=220 -> w=563 (Zara's large size)
          src = src.replace(/[?&]w=\d+/, '').replace(/[?&]ts=\d+/, '');
          // Clean up leftover ? or &
          src = src.replace(/[?&]$/, '').replace(/\?&/, '?');
          // Add high-res width
          src += (src.includes('?') ? '&' : '?') + 'w=563';
          if (!images.includes(src)) images.push(src);
        }
      }
      // Keep only the first image (main packshot)
      const finalImages = images.slice(0, 1);

      // Color from image alt text or product key
      const colors = [];
      const imgAlt = item.querySelector('img.media-image__image[alt]');
      if (imgAlt) {
        const alt = imgAlt.getAttribute('alt') || '';
        // Alt often contains color: "Ensemble robe courte grise à carreaux..."
        // We'll let the tagger handle color extraction from the title
      }

      // Extract color code from data-productkey if available
      // Format: "502202513-02180301111-p" - not directly useful for color name

      products.push({
        source: 'zara',
        external_id: externalId,
        title: title,
        description: null,
        brand: 'Zara',
        price: price,
        currency: 'EUR',
        original_url: productUrl,
        image_urls: finalImages,
        category: 'clothing',
        subcategory: subcategory,
        gender: gender,
        sizes: [],
        colors: colors,
        material: null,
        country: 'FR',
        language: 'fr',
        scraped_at: new Date().toISOString()
      });
    } catch(e) {
      console.warn('Error parsing product:', e);
    }
  }

  // Download as file
  const result = {
    source: 'zara',
    page_url: window.location.href,
    extracted_at: new Date().toISOString(),
    total: products.length,
    products: products
  };

  const json = JSON.stringify(result, null, 2);
  const blob = new Blob([json], {type: 'application/json'});
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = 'zara_products.json';
  a.click();

  console.log(`%c✅ ${products.length} produits Zara extraits et telecharges!`, 'color: green; font-size: 16px; font-weight: bold');
  console.table(products.map(p => ({
    title: p.title.substring(0, 50),
    price: p.price + '€',
    img: p.image_urls.length > 0 ? '✓' : '✗'
  })));

  return products;
})();
