// === StylAI - Zalando Single Product Extractor ===
// 1. Ouvre une page produit Zalando
// 2. Ouvre la console (F12 > Console)
// 3. Colle ce script et appuie sur Entree
// 4. Le JSON du produit est copie dans ton presse-papier

(function() {
  // Extract JSON-LD
  const jsonLdScripts = document.querySelectorAll('script[type="application/ld+json"]');
  let productData = null;

  for (const script of jsonLdScripts) {
    try {
      const data = JSON.parse(script.textContent);
      if (data['@type'] === 'Product') {
        productData = data;
        break;
      }
      if (Array.isArray(data)) {
        const found = data.find(d => d['@type'] === 'Product');
        if (found) { productData = found; break; }
      }
    } catch(e) {}
  }

  // Extract additional info from DOM
  const gender = window.location.pathname.includes('/homme') ? 'men'
    : window.location.pathname.includes('/femme') ? 'women' : 'unisex';

  // Try to get color from page
  let color = '';
  const colorEl = document.querySelector('[data-testid="pdp-color-picker-selected-color"], [class*="color" i]');
  if (colorEl) color = colorEl.textContent?.trim() || '';

  // Try to get sizes
  const sizes = [];
  document.querySelectorAll('[class*="size"] button, [data-testid*="size"] button, [class*="size"] label').forEach(el => {
    const text = el.textContent?.trim();
    if (text && text.length < 10) {
      sizes.push({
        size: text,
        available: !el.disabled && !el.classList.toString().includes('disabled')
      });
    }
  });

  // Try to get material/composition
  let material = '';
  const detailEls = document.querySelectorAll('[class*="detail"], [class*="attribute"], [class*="composition"]');
  for (const el of detailEls) {
    const text = el.textContent;
    if (text && (text.includes('%') && (text.includes('coton') || text.includes('polyester') ||
        text.includes('Cotton') || text.includes('Polyester') || text.includes('viscose')))) {
      material = text.trim().substring(0, 200);
      break;
    }
  }

  // Try to get category from breadcrumbs
  let category = 'clothing';
  let subcategory = '';
  const breadcrumbs = document.querySelectorAll('[class*="breadcrumb"] a, nav[aria-label*="breadcrumb"] a');
  if (breadcrumbs.length >= 2) {
    const last = breadcrumbs[breadcrumbs.length - 1];
    subcategory = last.textContent?.trim() || '';
  }

  // Build the complete product object
  const offers = productData?.offers;
  const offer = Array.isArray(offers) ? offers[0] : offers;

  const result = {
    source: 'zalando',
    external_id: productData?.sku || window.location.pathname.split('/').pop()?.replace('.html','') || '',
    title: productData?.name || document.querySelector('h1')?.textContent?.trim() || '',
    description: productData?.description || '',
    brand: (typeof productData?.brand === 'object' ? productData?.brand?.name : productData?.brand) || '',
    price: parseFloat(offer?.price || offer?.lowPrice || '0'),
    currency: offer?.priceCurrency || 'EUR',
    original_url: window.location.href,
    image_urls: (() => {
      let imgs = productData?.image;
      if (typeof imgs === 'string') return [imgs];
      if (Array.isArray(imgs)) return imgs.map(i => typeof i === 'string' ? i : i.url).filter(Boolean);
      // Fallback: get images from gallery
      const gallery = document.querySelectorAll('[data-testid*="gallery"] img, [class*="gallery"] img');
      return [...gallery].map(img => img.src).filter(s => s && s.includes('ztat.net')).slice(0, 6);
    })(),
    category: category,
    subcategory: subcategory,
    gender: gender,
    sizes: sizes,
    colors: color ? [color] : [],
    material: material,
    country: 'FR',
    language: 'fr',
    scraped_at: new Date().toISOString(),
    _raw_json_ld: productData
  };

  const json = JSON.stringify(result, null, 2);
  copy(json);
  console.log('Product data copied to clipboard!');
  console.log(result);
  return result;
})();
