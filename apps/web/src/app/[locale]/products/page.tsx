import { useTranslations } from "next-intl";
import { ProductCard } from "@/components/product/product-card";
import { getProducts, searchProducts } from "@/lib/api";
import { ProductFilters } from "@/components/product/product-filters";

export default async function ProductsPage({
  searchParams,
}: {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  const params = await searchParams;
  const query = typeof params.q === "string" ? params.q : undefined;
  const page = typeof params.page === "string" ? params.page : "1";
  const gender = typeof params.gender === "string" ? params.gender : undefined;
  const brand = typeof params.brand === "string" ? params.brand : undefined;

  const apiParams: Record<string, string> = { page, page_size: "20" };
  if (gender) apiParams.gender = gender;
  if (brand) apiParams.brand = brand;

  let products;
  if (query) {
    const searchData = await searchProducts(query, { limit: "40", ...apiParams }).catch(() => null);
    products = searchData ? searchData.results.map((r) => r.product) : [];
  } else {
    const listData = await getProducts(apiParams).catch(() => null);
    products = listData?.products ?? [];
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <PageHeader query={query} count={products.length} />
      <ProductFilters />
      {products.length === 0 ? (
        <NoResults />
      ) : (
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4 mt-6">
          {products.map((p) => (
            <ProductCard key={p.id} product={p} />
          ))}
        </div>
      )}
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
