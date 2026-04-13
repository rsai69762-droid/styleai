import { useTranslations } from "next-intl";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

export default function ProfilePage() {
  const t = useTranslations("profile");

  // MVP: static profile display (auth integration in Phase 5)
  return (
    <div className="container mx-auto px-4 py-8 max-w-2xl">
      <h1 className="text-3xl font-bold mb-8">{t("title")}</h1>

      <div className="space-y-6">
        <Card>
          <CardContent className="p-6">
            <h2 className="text-lg font-semibold mb-4">{t("style")}</h2>
            <div className="flex flex-wrap gap-2">
              {["casual", "bohème", "fleuri", "vintage"].map((tag) => (
                <Badge key={tag} variant="secondary">
                  {tag}
                </Badge>
              ))}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <h2 className="text-lg font-semibold mb-4">{t("colors")}</h2>
            <div className="flex gap-3">
              {[
                { name: "rose", color: "#f9a8d4" },
                { name: "blanc", color: "#ffffff" },
                { name: "bleu", color: "#93c5fd" },
                { name: "beige", color: "#d4c5a9" },
              ].map((c) => (
                <div key={c.name} className="text-center">
                  <div
                    className="w-10 h-10 rounded-full border"
                    style={{ backgroundColor: c.color }}
                  />
                  <span className="text-xs text-muted-foreground mt-1">
                    {c.name}
                  </span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <h2 className="text-lg font-semibold mb-4">{t("budget")}</h2>
            <p className="text-2xl font-bold">20€ - 80€</p>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <h2 className="text-lg font-semibold mb-4">{t("brands")}</h2>
            <div className="flex flex-wrap gap-2">
              {["ASOS DESIGN", "Zara", "H&M", "Mango"].map((b) => (
                <Badge key={b} variant="outline">
                  {b}
                </Badge>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
