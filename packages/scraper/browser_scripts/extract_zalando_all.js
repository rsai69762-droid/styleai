// === StylAI - Zalando BULK Product Extractor ===
// 1. Ouvre une page listing Zalando (ex: https://www.zalando.fr/mode-femme/)
// 2. SCROLL JUSQU'EN BAS pour charger un max de produits
// 3. Ouvre la console (F12 > Console)
// 4. Colle ce script et appuie sur Entree
// 5. Le JSON est telecharge automatiquement en fichier

(function() {
  const products = [];
  const seen = new Set();

  const url = window.location.href;
  const gender = url.includes('homme') || url.includes('/men') ? 'men'
    : url.includes('femme') || url.includes('/women') ? 'women' : 'unisex';

  const pathParts = window.location.pathname.split('/').filter(Boolean);
  const category = 'clothing';
  let subcategory = pathParts[pathParts.length - 1] || '';
  if (subcategory.startsWith('mode-')) subcategory = '';

  // Zalando uses <article> tags for product cards
  const articles = document.querySelectorAll('article');
  console.log(`Found ${articles.length} article elements`);

  for (const article of articles) {
    try {
      // Get the FIRST link with .html (main product link)
      const link = article.querySelector('a[href*=".html"]');
      if (!link) continue;
      const href = link.getAttribute('href');
      const productUrl = href.startsWith('http') ? href : 'https://www.zalando.fr' + href;

      if (seen.has(productUrl)) continue;
      seen.add(productUrl);

      // External ID: last part of URL before .html (e.g. "qm421n01l-k12")
      const urlParts = href.replace('.html', '').split('/').pop().split('-');
      const externalId = urlParts.slice(-2).join('-') || href.replace('.html','').split('/').pop();

      // Brand and title are inside <h3> with two <span> children
      // First span = brand (bold), second span = product name
      const h3 = article.querySelector('h3');
      let brand = '';
      let title = '';
      if (h3) {
        const spans = h3.querySelectorAll('span');
        if (spans.length >= 2) {
          brand = spans[0].textContent.trim();
          title = spans[1].textContent.trim();
        } else if (spans.length === 1) {
          title = spans[0].textContent.trim();
        } else {
          title = h3.textContent.trim();
        }
      }

      // Price: find spans containing "€" inside the <header> or <section>
      let price = 0;
      let originalPrice = 0;
      const section = article.querySelector('section');
      if (section) {
        // Get all price-like spans (contain € symbol)
        const allSpans = section.querySelectorAll('span');
        for (const span of allSpans) {
          const text = span.textContent.trim();
          if (text.includes('€') && !text.includes('%') && !text.includes('Dernier')) {
            const priceVal = parseFloat(text.replace(/[^\d,]/g, '').replace(',', '.'));
            if (priceVal > 0) {
              if (price === 0) {
                price = priceVal; // First price = current/sale price
              } else if (originalPrice === 0) {
                originalPrice = priceVal; // Second = original price
              }
            }
          }
        }
      }

      // Images: get main product image from srcset
      const images = [];
      const imgEls = article.querySelectorAll('img[src*="ztat.net"]');
      for (const img of imgEls) {
        // Prefer srcset for higher quality, get the largest
        const srcset = img.getAttribute('srcset');
        if (srcset) {
          // Get the last (largest) srcset entry
          const entries = srcset.split(',').map(s => s.trim().split(' ')[0]);
          const best = entries[entries.length - 1] || entries[0];
          if (best && !images.includes(best)) images.push(best);
        } else if (img.src && !images.includes(img.src)) {
          images.push(img.src);
        }
      }
      // Keep only the main packshot (first large image), skip color variant thumbs
      const mainImages = images.filter(u => u.includes('imwidth=') && !u.includes('imwidth=50'));
      const finalImages = mainImages.length > 0 ? mainImages.slice(0, 1) : images.slice(0, 1);

      // Extract color from the alt text of variant thumbnails
      const colors = [];
      const altTexts = article.querySelectorAll('img[alt]');
      for (const img of altTexts) {
        const alt = img.getAttribute('alt') || '';
        // Product alt text format: "Product Name - color"
        const dashParts = alt.split(' - ');
        if (dashParts.length >= 2) {
          const color = dashParts[dashParts.length - 1].trim();
          if (color && !colors.includes(color) && color.length < 30) {
            colors.push(color);
          }
        }
      }

      if (!title || price === 0) {
        console.warn('Skipping incomplete product:', { title, price, href });
        continue;
      }

      products.push({
        source: 'zalando',
        external_id: externalId,
        title: brand ? `${brand} - ${title}` : title,
        description: null,
        brand: brand,
        price: price,
        currency: 'EUR',
        original_url: productUrl,
        image_urls: finalImages,
        category: category,
        subcategory: subcategory,
        gender: gender,
        sizes: [],
        colors: [...new Set(colors)],
        material: null,
        country: 'FR',
        language: 'fr',
        scraped_at: new Date().toISOString()
      });
    } catch(e) {
      console.warn('Error parsing article:', e);
    }
  }

  // Download as file
  const result = {
    source: 'zalando',
    page_url: window.location.href,
    extracted_at: new Date().toISOString(),
    total: products.length,
    products: products
  };

  const json = JSON.stringify(result, null, 2);
  const blob = new Blob([json], {type: 'application/json'});
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = 'zalando_products.json';
  a.click();

  console.log(`%c✅ ${products.length} produits extraits et telecharges!`, 'color: green; font-size: 16px; font-weight: bold');
  console.table(products.map(p => ({
    brand: p.brand,
    title: p.title.substring(0, 50),
    price: p.price + '€',
    colors: p.colors.join(', '),
    img: p.image_urls.length > 0 ? '✓' : '✗'
  })));

  return products;
})();
