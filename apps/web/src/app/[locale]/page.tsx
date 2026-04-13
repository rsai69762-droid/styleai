import { useTranslations } from "next-intl";
import { Link } from "@/i18n/navigation";
import { buttonVariants } from "@/components/ui/button";
import { ProductCard } from "@/components/product/product-card";
import { getProducts, searchProducts, type Product, type SearchResult } from "@/lib/api";
import { cn } from "@/lib/utils";

export default async function HomePage() {
  const [productsData, trendingData] = await Promise.all([
    getProducts({ page_size: "8", sort_by: "created_at" }).catch(() => null),
    searchProducts("tendance ete", { limit: "4" }).catch(() => null),
  ]);

  return (
    <div>
      {/* Hero */}
      <section className="relative overflow-hidden bg-gradient-to-br from-purple-50 via-pink-50 to-orange-50 dark:from-purple-950 dark:via-pink-950 dark:to-orange-950">
        <div className="container mx-auto px-4 py-20 text-center">
          <h1 className="text-4xl md:text-6xl font-bold tracking-tight">
            <span className="bg-gradient-to-r from-purple-600 to-pink-500 bg-clip-text text-transparent">
              StylAI
            </span>
          </h1>
          <HeroContent />
        </div>
      </section>

      {/* Trending */}
      {trendingData && trendingData.results.length > 0 && (
        <section className="container mx-auto px-4 py-12">
          <TrendingSection results={trendingData.results} />
        </section>
      )}

      {/* New arrivals */}
      {productsData && productsData.products.length > 0 && (
        <section className="container mx-auto px-4 py-12">
          <NewArrivalsSection products={productsData.products} />
        </section>
      )}
    </div>
  );
}

function HeroContent() {
  const t = useTranslations("home");
  const tNav = useTranslations("nav");
  return (
    <>
      <p className="mt-4 text-lg md:text-xl text-muted-foreground max-w-2xl mx-auto">
        {t("heroSub")}
      </p>
      <div className="mt-8 flex gap-4 justify-center">
        <Link href="/recommendations" className={cn(buttonVariants({ size: "lg" }))}>
          {t("cta")}
        </Link>
        <Link href="/products" className={cn(buttonVariants({ variant: "outline", size: "lg" }))}>
          {tNav("products")}
        </Link>
      </div>
    </>
  );
}

function TrendingSection({ results }: { results: SearchResult[] }) {
  const t = useTranslations("home");
  return (
    <>
      <h2 className="text-2xl font-bold mb-6">{t("trending")}</h2>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {results.map((r) => (
          <ProductCard key={r.product.id} product={r.product} />
        ))}
      </div>
    </>
  );
}

function NewArrivalsSection({ products }: { products: Product[] }) {
  const t = useTranslations("home");
  const tCommon = useTranslations("common");
  return (
    <>
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold">{t("newArrivals")}</h2>
        <Link href="/products" className={cn(buttonVariants({ variant: "ghost" }))}>
          {tCommon("seeMore")} &rarr;
        </Link>
      </div>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {products.map((p) => (
          <ProductCard key={p.id} product={p} />
        ))}
      </div>
    </>
  );
}
