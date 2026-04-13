import { createNavigation } from "next-intl/navigation";
import { defineRouting } from "next-intl/routing";
import { locales, defaultLocale } from "./config";

export const routing = defineRouting({
  locales,
  defaultLocale,
  pathnames: {
    "/": "/",
    "/products": {
      fr: "/produits",
      en: "/products",
      de: "/produkte",
      es: "/productos",
      it: "/prodotti",
    },
    "/products/[slug]": {
      fr: "/produits/[slug]",
      en: "/products/[slug]",
      de: "/produkte/[slug]",
      es: "/productos/[slug]",
      it: "/prodotti/[slug]",
    },
    "/recommendations": {
      fr: "/recommandations",
      en: "/recommendations",
      de: "/empfehlungen",
      es: "/recomendaciones",
      it: "/raccomandazioni",
    },
    "/login": {
      fr: "/connexion",
      en: "/login",
      de: "/anmelden",
      es: "/iniciar-sesion",
      it: "/accedi",
    },
    "/profile": {
      fr: "/profil",
      en: "/profile",
      de: "/profil",
      es: "/perfil",
      it: "/profilo",
    },
  },
});

export const { Link, redirect, usePathname, useRouter } =
  createNavigation(routing);
