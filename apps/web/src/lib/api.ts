const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

async function fetchAPI<T>(path: string, options?: RequestInit): Promise<T> {
  console.log("API_BASE " , API_BASE)
  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    signal: AbortSignal.timeout(5000),
    headers: {
      "Content-Type": "application/json",
      ...options?.headers,
    },
  });
  if (!res.ok) {
    throw new Error(`API error ${res.status}: ${res.statusText}`);
  }
  return res.json();
}

// Types matching the FastAPI schemas
export interface Product {
  id: string;
  source: string;
  slug: string;
  title: string;
  description: string | null;
  brand: string | null;
  price_cents: number;
  currency: string;
  original_url: string;
  affiliate_url: string | null;
  image_urls: string[];
  category: string | null;
  subcategory: string | null;
  gender: string | null;
  sizes: unknown[];
  colors: string[];
  material: string | null;
  tags: string[];
  language: string;
  scraped_at: string;
  is_available: boolean;
}

export interface ProductListResponse {
  products: Product[];
  total: number;
  page: number;
  page_size: number;
}

export interface SearchResult {
  product: Product;
  score: number;
}

export interface SearchResponse {
  results: SearchResult[];
  query: string;
  total: number;
}

export interface RecommendationItem {
  id: string;
  product: Product;
  score: number;
  reason: string | null;
  agent_run_id: string | null;
  created_at: string;
}

export interface RecommendationResponse {
  agent_run_id: string;
  recommendations: RecommendationItem[];
  context: {
    weather?: { temperature_c: number; is_rainy: boolean; season: string };
    trends?: string[];
    search_queries?: string[];
  };
}

// API functions
export function getProducts(params?: Record<string, string>) {
  const qs = params ? "?" + new URLSearchParams(params).toString() : "";
  return fetchAPI<ProductListResponse>(`/products${qs}`);
}

export function getProduct(slug: string) {
  return fetchAPI<Product>(`/products/${slug}`);
}

export function searchProducts(query: string, params?: Record<string, string>) {
  const allParams = { q: query, ...params };
  const qs = new URLSearchParams(allParams).toString();
  return fetchAPI<SearchResponse>(`/products/search?${qs}`);
}

export function getSimilarProducts(productId: string, limit = 6) {
  return fetchAPI<SearchResult[]>(`/products/${productId}/similar?limit=${limit}`);
}

export function generateRecommendations(
  token: string,
  body: { occasion?: string; mood?: string }
) {
  return fetchAPI<RecommendationResponse>("/recommendations/generate", {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
    body: JSON.stringify(body),
  });
}

export function getRecommendations(token: string) {
  return fetchAPI<RecommendationItem[]>("/recommendations", {
    headers: { Authorization: `Bearer ${token}` },
  });
}

export function formatPrice(cents: number, currency = "EUR", locale = "fr-FR") {
  return new Intl.NumberFormat(locale, {
    style: "currency",
    currency,
  }).format(cents / 100);
}
