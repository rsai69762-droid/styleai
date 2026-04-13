"use client";

import { useTranslations } from "next-intl";
import { useRouter, usePathname } from "@/i18n/navigation";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { useState } from "react";

export function ProductFilters() {
  const t = useTranslations("products");
  const tNav = useTranslations("nav");
  const router = useRouter();
  const pathname = usePathname();
  const [search, setSearch] = useState("");

  function onSearch(e: React.FormEvent) {
    e.preventDefault();
    if (search.trim()) {
      router.push(`/products?q=${encodeURIComponent(search.trim())}` as "/products");
    }
  }

  return (
    <form onSubmit={onSearch} className="flex gap-2 max-w-md">
      <Input
        value={search}
        onChange={(e) => setSearch(e.target.value)}
        placeholder={tNav("search")}
        className="flex-1"
      />
      <Button type="submit" size="sm">
        {t("filters")}
      </Button>
    </form>
  );
}
