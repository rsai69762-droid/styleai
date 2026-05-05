"use client";

import { useState } from "react";
import { useTranslations } from "next-intl";
import { Button } from "@/components/ui/button";
import { ProductCard } from "@/components/product/product-card";
import { getProducts, type Product } from "@/lib/api";

interface ProductsGridProps {
  initialProducts: Product[];
  initialPage: number;
  pageSize: number;
  total: number;
  filters: { gender?: string; brand?: string };
}

export function ProductsGrid({
  initialProducts,
  initialPage,
  pageSize,
  total,
  filters,
}: ProductsGridProps) {
  const tCommon = useTranslations("common");
  const tProducts = useTranslations("products");
  const [products, setProducts] = useState<Product[]>(initialProducts);
  const [page, setPage] = useState(initialPage);
  const [loading, setLoading] = useState(false);

  const hasMore = products.length < total;

  async function loadMore() {
    setLoading(true);
    try {
      const next = page + 1;
      const params: Record<string, string> = {
        page: String(next),
        page_size: String(pageSize),
        sort_by: "created_at",
      };
      if (filters.gender) params.gender = filters.gender;
      if (filters.brand) params.brand = filters.brand;
      const data = await getProducts(params);
      setProducts((prev) => [...prev, ...data.products]);
      setPage(next);
    } finally {
      setLoading(false);
    }
  }

  return (
    <>
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4 mt-6">
        {products.map((p) => (
          <ProductCard key={p.id} product={p} />
        ))}
      </div>
      {hasMore && (
        <div className="flex justify-center mt-8">
          <Button
            onClick={loadMore}
            disabled={loading}
            variant="outline"
            size="lg"
          >
            {loading ? tCommon("loading") : tProducts("loadMore")}
          </Button>
        </div>
      )}
    </>
  );
}
