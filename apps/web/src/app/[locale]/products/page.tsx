import { useTranslations } from "next-intl";
import { ProductCard } from "@/components/product/product-card";
import { ProductsGrid } from "@/components/product/products-grid";
import { getProducts, searchProducts, type Product } from "@/lib/api";
import { ProductFilters } from "@/components/product/product-filters";

const PAGE_SIZE = 20;

export default async function ProductsPage({
  searchParams,
}: {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  const params = await searchParams;
  const query = typeof params.q === "string" ? params.q : undefined;
  const pageParam = typeof params.page === "string" ? params.page : "1";
  const page = Math.max(1, Number.parseInt(pageParam, 10) || 1);
  const gender = typeof params.gender === "string" ? params.gender : undefined;
  const brand = typeof params.brand === "string" ? params.brand : undefined;

  if (query) {
    const searchData = await searchProducts(query, {
      limit: String(PAGE_SIZE * 2),
    }).catch(() => null);
    const products = searchData ? searchData.results.map((r) => r.product) : [];
    return (
      <ProductsPageShell query={query} count={products.length}>
        <StaticGrid products={products} />
      </ProductsPageShell>
    );
  }

  const apiParams: Record<string, string> = {
    page: String(page),
    page_size: String(PAGE_SIZE),
    sort_by: "created_at",
  };
  if (gender) apiParams.gender = gender;
  if (brand) apiParams.brand = brand;

  const listData = await getProducts(apiParams).catch(() => null);
  const products = listData?.products ?? [];
  const total = listData?.total ?? products.length;

  return (
    <ProductsPageShell count={total}>
      {products.length === 0 ? (
        <NoResults />
      ) : (
        <ProductsGrid
          initialProducts={products}
          initialPage={page}
          pageSize={PAGE_SIZE}
          total={total}
          filters={{ gender, brand }}
        />
      )}
    </ProductsPageShell>
  );
}

function ProductsPageShell({
  query,
  count,
  children,
}: {
  query?: string;
  count: number;
  children: React.ReactNode;
}) {
  return (
    <div className="container mx-auto px-4 py-8">
      <PageHeader query={query} count={count} />
      <ProductFilters />
      {children}
    </div>
  );
}

function StaticGrid({ products }: { products: Product[] }) {
  if (products.length === 0) return <NoResults />;
  return (
    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4 mt-6">
      {products.map((p) => (
        <ProductCard key={p.id} product={p} />
      ))}
    </div>
  );
}

function PageHeader({ query, count }: { query?: string; count: number }) {
  const t = useTranslations("products");
  return (
    <div className="mb-4">
      <h1 className="text-3xl font-bold">
        {query ? `"${query}"` : t("title")}
      </h1>
      <p className="text-muted-foreground mt-1">
        {t("results", { count })}
      </p>
    </div>
  );
}

function NoResults() {
  const t = useTranslations("products");
  return (
    <div className="py-20 text-center text-muted-foreground">
      <p className="text-lg">{t("noResults")}</p>
    </div>
  );
}
