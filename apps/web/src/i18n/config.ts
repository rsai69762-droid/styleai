export const locales = ["fr", "en", "de", "es", "it"] as const;
export type Locale = (typeof locales)[number];
export const defaultLocale: Locale = "fr";
