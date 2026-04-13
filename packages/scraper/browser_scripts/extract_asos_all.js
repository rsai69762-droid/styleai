// === StylAI - ASOS BULK Product Extractor ===
// 1. Ouvre une page listing ASOS (ex: https://www.asos.com/fr/femme/robes/cat/?cid=8799)
// 2. SCROLL JUSQU'EN BAS pour charger un max de produits
// 3. Ouvre la console (F12 > Console)
// 4. Colle ce script et appuie sur Entree
// 5. Le JSON est telecharge automatiquement en fichier

(function() {
  const products = [];
  const seen = new Set();

  const url = window.location.href;
  const pathname = window.location.pathname;

  // Gender detection from URL
  const gender = pathname.includes('/homme') || pathname.includes('/men') ? 'men'
    : pathname.includes('/femme') || pathname.includes('/women') ? 'women' : 'unisex';

  // Category detection from URL path
  // e.g. /fr/femme/robes/cat/ -> "robes"
  const pathParts = pathname.split('/').filter(Boolean);
  let subcategory = '';
  for (let i = pathParts.length - 1; i >= 0; i--) {
    if (pathParts[i] !== 'cat' && pathParts[i] !== 'fr' && pathParts[i] !== 'femme' && pathParts[i] !== 'homme') {
      subcategory = pathParts[i];
      break;
    }
  }

  // ASOS uses <li id="product-{id}"> for product cards
  const items = document.querySelectorAll('li[id^="product-"]');
  console.log(`Found ${items.length} product elements`);

  for (const item of items) {
    try {
      // External ID from li id attribute: "product-210460581" -> "210460581"
      const liId = item.getAttribute('id') || '';
      const externalId = liId.replace('product-', '');
      if (!externalId) continue;

      // Product link - contains /prd/ in href
      const link = item.querySelector('a[href*="/prd/"]');
      if (!link) continue;

      const href = link.getAttribute('href');
      // Clean URL: remove query params and fragments
      const cleanHref = href.split('?')[0].split('#')[0];
      const productUrl = cleanHref.startsWith('http') ? cleanHref : 'https://www.asos.com' + cleanHref;

      if (seen.has(externalId)) continue;
      seen.add(externalId);

      // Title from the product description paragraph
      // Classes are obfuscated, so we use the paragraph structure
      const descP = item.querySelector('p[class*="productDescription"], p[id*="pta-product"][id$="-0"]');
      let fullTitle = '';
      if (descP) {
        fullTitle = descP.textContent.trim();
      } else {
        // Fallback: aria-label on the link (format: "Brand - Title, Prix XX,XX €")
        const ariaLabel = link.getAttribute('aria-label') || '';
        fullTitle = ariaLabel.split(', Prix')[0].trim();
      }

      if (!fullTitle) continue;

      // Brand and title: split on first " - "
      let brand = '';
      let title = fullTitle;
      const dashIndex = fullTitle.indexOf(' - ');
      if (dashIndex > 0) {
        brand = fullTitle.substring(0, dashIndex).trim();
        title = fullTitle.substring(dashIndex + 3).trim();
      }

      // Price: look for spans containing "€"
      let price = 0;
      let originalPrice = 0;
      const priceSpans = item.querySelectorAll('span[class*="price"]');
      for (const span of priceSpans) {
        const text = span.textContent.trim();
        if (text.includes('€') && !text.includes('%')) {
          const priceVal = parseFloat(text.replace(/[^\d,]/g, '').replace(',', '.'));
          if (priceVal > 0) {
            if (price === 0) {
              price = priceVal;
            } else if (originalPrice === 0 && priceVal !== price) {
              originalPrice = priceVal;
            }
          }
        }
      }
      // Fallback: parse price from aria-label
      if (price === 0) {
        const ariaLabel = link.getAttribute('aria-label') || '';
        const priceMatch = ariaLabel.match(/(\d+[,.]?\d*)\s*€/);
        if (priceMatch) {
          price = parseFloat(priceMatch[1].replace(',', '.'));
        }
      }

      // Images: get from srcset of product images
      const images = [];
      const imgEls = item.querySelectorAll('img[src*="asos-media.com"]');
      for (const img of imgEls) {
        const srcset = img.getAttribute('srcset');
        if (srcset) {
          // Get the largest image from srcset
          const entries = srcset.split(',').map(s => s.trim().split(/\s+/));
          let bestUrl = '';
          let bestWidth = 0;
          for (const [imgUrl, widthStr] of entries) {
            const w = parseInt((widthStr || '').replace('w', ''));
            if (w > bestWidth) {
              bestWidth = w;
              bestUrl = imgUrl;
            }
          }
          if (bestUrl) {
            const fullUrl = bestUrl.startsWith('//') ? 'https:' + bestUrl : bestUrl;
            if (!images.includes(fullUrl)) images.push(fullUrl);
          }
        } else if (img.src) {
          const fullSrc = img.src.startsWith('//') ? 'https:' + img.src : img.src;
          if (!images.includes(fullSrc)) images.push(fullSrc);
        }
      }
      // Keep only the first image (main packshot), skip hover image
      const finalImages = images.slice(0, 1);

      // Color: try to extract from URL fragment (colourWayId) or image alt text
      const colors = [];
      const firstImg = item.querySelector('img[alt]');
      if (firstImg) {
        const alt = firstImg.getAttribute('alt') || '';
        // Alt format: "BRAND - Title - color" sometimes at the end
        // Not always present on ASOS, skip if not clear
      }

      if (!fullTitle || price === 0) {
        console.warn('Skipping incomplete product:', { fullTitle, price, href });
        continue;
      }

      products.push({
        source: 'asos',
        external_id: externalId,
        title: brand ? `${brand} - ${title}` : title,
        description: null,
        brand: brand,
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
    source: 'asos',
    page_url: window.location.href,
    extracted_at: new Date().toISOString(),
    total: products.length,
    products: products
  };

  const json = JSON.stringify(result, null, 2);
  const blob = new Blob([json], {type: 'application/json'});
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = 'asos_products.json';
  a.click();

  console.log(`%c✅ ${products.length} produits ASOS extraits et telecharges!`, 'color: green; font-size: 16px; font-weight: bold');
  console.table(products.map(p => ({
    brand: p.brand,
    title: p.title.substring(0, 50),
    price: p.price + '€',
    img: p.image_urls.length > 0 ? '✓' : '✗'
  })));

  return products;
})();
