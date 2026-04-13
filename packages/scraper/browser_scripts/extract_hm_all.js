// === StylAI - H&M BULK Product Extractor ===
// 1. Ouvre une page listing H&M
//    ex: https://www2.hm.com/fr_fr/femme/catalogue-par-produit/tops.html
// 2. SCROLL JUSQU'EN BAS pour charger tous les produits
//    (ou cliquer "Charger plus" si present)
// 3. Ouvre la console (F12 > Console)
// 4. Colle ce script et appuie sur Entree
// 5. Le JSON est telecharge automatiquement

(function() {
  const products = [];
  const seen = new Set();

  const url = window.location.href;
  const pathname = window.location.pathname;

  // Gender detection from URL
  let gender = 'women';
  if (pathname.includes('/homme') || pathname.includes('/men')) {
    gender = 'men';
  } else if (pathname.includes('/femme') || pathname.includes('/women') || pathname.includes('/ladies')) {
    gender = 'women';
  }

  // Subcategory from URL path
  // e.g. /fr_fr/femme/catalogue-par-produit/tops.html -> "tops"
  let subcategory = '';
  const pathMatch = pathname.match(/\/([^/]+)\.html$/);
  if (pathMatch) {
    subcategory = pathMatch[1].replace(/-/g, ' ');
  }

  // H&M uses <article data-articlecode="...">
  const items = document.querySelectorAll('article[data-articlecode]');
  console.log(`Found ${items.length} product elements`);

  for (const item of items) {
    try {
      const externalId = item.getAttribute('data-articlecode');
      if (!externalId || seen.has(externalId)) continue;
      seen.add(externalId);

      // Product link
      const link = item.querySelector('a[href*="/productpage."]');
      if (!link) continue;
      const href = link.getAttribute('href');
      const productUrl = href.startsWith('http')
        ? href.split('?')[0]
        : 'https://www2.hm.com' + href.split('?')[0];

      // Title from <h2> inside article
      const titleEl = item.querySelector('h2');
      const title = titleEl ? titleEl.textContent.trim() : '';
      if (!title) continue;

      // Price: span with price text containing "€"
      let price = 0;
      let originalPrice = 0;

      // Look for sale price (red) and original price (strikethrough)
      const priceSpans = item.querySelectorAll('span[class*="dfdb90"], span[translate="no"]');
      for (const span of priceSpans) {
        const text = span.textContent.trim();
        if (text.includes('€')) {
          const val = parseFloat(text.replace(/[^\d,]/g, '').replace(',', '.'));
          if (val > 0) {
            if (price === 0) {
              price = val;
            } else if (originalPrice === 0 && val !== price) {
              originalPrice = Math.max(price, val);
              price = Math.min(price, val);
            }
          }
        }
      }

      // Fallback: any text with € inside the article price area
      if (price === 0) {
        const allSpans = item.querySelectorAll('p span');
        for (const span of allSpans) {
          const text = span.textContent.trim();
          if (text.includes('€')) {
            const val = parseFloat(text.replace(/[^\d,]/g, '').replace(',', '.'));
            if (val > 0) { price = val; break; }
          }
        }
      }

      if (price === 0) {
        console.warn('Skipping product without price:', title);
        continue;
      }

      // Images: get best from srcset (image.hm.com)
      const images = [];
      const imgEl = item.querySelector('img[srcset*="image.hm.com"]');
      if (imgEl) {
        const srcset = imgEl.getAttribute('srcset');
        if (srcset) {
          // Parse srcset entries, pick the 564w version (good quality, not too large)
          const entries = srcset.split(',').map(s => s.trim().split(/\s+/));
          let bestUrl = '';
          let bestWidth = 0;
          const targetWidth = 564;
          for (const [imgUrl, widthStr] of entries) {
            const w = parseInt((widthStr || '').replace('w', ''));
            // Pick closest to target, or largest under 800
            if (w === targetWidth) {
              bestUrl = imgUrl;
              bestWidth = w;
              break;
            }
            if (w > bestWidth && w <= 820) {
              bestWidth = w;
              bestUrl = imgUrl;
            }
          }
          if (bestUrl) {
            const fullUrl = bestUrl.startsWith('//') ? 'https:' + bestUrl : bestUrl;
            images.push(fullUrl);
          }
        }
        // Fallback to src
        if (images.length === 0 && imgEl.src && imgEl.src.includes('image.hm.com')) {
          images.push(imgEl.src);
        }
      }

      // Color from img alt text: "Top à bretelles fines avec dentelle - Noir"
      const colors = [];
      if (imgEl) {
        const alt = imgEl.getAttribute('alt') || imgEl.getAttribute('data-alttext') || '';
        const dashParts = alt.split(' - ');
        if (dashParts.length >= 2) {
          const colorText = dashParts[dashParts.length - 1].trim();
          if (colorText && colorText.length < 40) {
            colors.push(colorText);
          }
        }
      }

      // H&M data-category: "ladies_tops_vests" -> use as fallback subcategory
      const dataCategory = item.getAttribute('data-category') || '';

      products.push({
        source: 'hm',
        external_id: externalId,
        title: title,
        description: null,
        brand: 'H&M',
        price: price,
        currency: 'EUR',
        original_url: productUrl,
        image_urls: images,
        category: 'clothing',
        subcategory: subcategory || dataCategory.replace(/_/g, ' '),
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
    source: 'hm',
    page_url: window.location.href,
    extracted_at: new Date().toISOString(),
    total: products.length,
    products: products
  };

  const json = JSON.stringify(result, null, 2);
  const blob = new Blob([json], {type: 'application/json'});
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = 'hm_products.json';
  a.click();

  console.log(`%c✅ ${products.length} produits H&M extraits et telecharges!`, 'color: green; font-size: 16px; font-weight: bold');
  console.table(products.map(p => ({
    title: p.title.substring(0, 50),
    price: p.price + '€',
    color: p.colors[0] || '-',
    img: p.image_urls.length > 0 ? '✓' : '✗'
  })));

  return products;
})();
