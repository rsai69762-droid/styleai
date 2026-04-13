"use client";

import { useLocale } from "next-intl";
import { usePathname, useRouter } from "@/i18n/navigation";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { locales, type Locale } from "@/i18n/config";

const localeLabels: Record<Locale, string> = {
  fr: "FR",
  en: "EN",
  de: "DE",
  es: "ES",
  it: "IT",
};

export function LocaleSwitcher() {
  const locale = useLocale() as Locale;
  const pathname = usePathname();
  const router = useRouter();

  function onChange(newLocale: Locale) {
    router.replace(pathname as "/", { locale: newLocale });
  }

  return (
    <DropdownMenu>
      <DropdownMenuTrigger className="inline-flex items-center justify-center rounded-lg px-2 py-1 text-xs font-medium hover:bg-muted">
        {localeLabels[locale]}
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end">
        {locales.map((l) => (
          <DropdownMenuItem
            key={l}
            onClick={() => onChange(l)}
            className={l === locale ? "font-bold" : ""}
          >
            {localeLabels[l]}
          </DropdownMenuItem>
        ))}
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
