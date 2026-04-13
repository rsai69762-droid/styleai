// === StylAI - Zalando Product Extractor ===
// 1. Ouvre une page listing Zalando (ex: https://www.zalando.fr/mode-femme/)
// 2. Scrolle jusqu'en bas pour charger tous les produits
// 3. Ouvre la console (F12 > Console)
// 4. Colle ce script et appuie sur Entree
// 5. Le JSON est copie dans ton presse-papier

(function() {
  const products = [];

  // Select all product card links
  const cards = document.querySelectorAll('article a[href*=".html"]');

  // Also try alternative selectors
  const altCards = document.querySelectorAll('a[href$=".html"][class*="tile"], a[href$=".html"][data-testid]');

  const allLinks = new Set();
  [...cards, ...altCards].forEach(a => {
    const href = a.getAttribute('href');
    if (href && href.endsWith('.html') && !href.includes('/faq/') && !href.includes('/aide/')) {
      allLinks.add(href.startsWith('http') ? href : 'https://www.zalando.fr' + href);
    }
  });

  console.log(`Found ${allLinks.size} product URLs`);

  const result = {
    source: 'zalando',
    page_url: window.location.href,
    extracted_at: new Date().toISOString(),
    product_urls: [...allLinks]
  };

  const json = JSON.stringify(result, null, 2);
  copy(json);
  console.log('Copied to clipboard! Paste it to the scraper.');
  console.log(json);
})();
