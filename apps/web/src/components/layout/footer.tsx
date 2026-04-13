import { useTranslations } from "next-intl";

export function Footer() {
  const t = useTranslations("footer");

  return (
    <footer className="border-t py-6 text-sm text-muted-foreground">
      <div className="container mx-auto flex flex-col md:flex-row items-center justify-between gap-4 px-4">
        <p className="font-medium text-foreground">
          <span className="bg-gradient-to-r from-purple-600 to-pink-500 bg-clip-text text-transparent">
            StylAI
          </span>{" "}
          &copy; {new Date().getFullYear()}
        </p>
        <div className="flex gap-6">
          <span>{t("about")}</span>
          <span>{t("privacy")}</span>
          <span>{t("terms")}</span>
          <span>{t("contact")}</span>
        </div>
      </div>
    </footer>
  );
}
