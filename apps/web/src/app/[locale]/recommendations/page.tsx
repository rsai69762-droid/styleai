"use client";

import { useState } from "react";
import { useTranslations } from "next-intl";
import Image from "next/image";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Link } from "@/i18n/navigation";
import { useAuth } from "@/components/auth/auth-provider";
import {
  type RecommendationItem,
  type RecommendationResponse,
  formatPrice,
} from "@/lib/api";

const API_BASE =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

export default function RecommendationsPage() {
  const t = useTranslations("recommendations");
  const { session } = useAuth();
  const [occasion, setOccasion] = useState<string>("");
  const [mood, setMood] = useState<string>("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<RecommendationResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function generate() {
    if (!session) return;
    setLoading(true);
    setError(null);
    try {
      const body: Record<string, string> = {};
      if (occasion) body.occasion = occasion;
      if (mood) body.mood = mood;

      const res = await fetch(`${API_BASE}/recommendations/generate`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${session.access_token}`,
        },
        body: JSON.stringify(body),
      });

      if (!res.ok) throw new Error(`Error ${res.status}`);
      const data: RecommendationResponse = await res.json();
      setResult(data);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  }

  const occasions = [
    { value: "casual", label: t("occasions.casual") },
    { value: "work", label: t("occasions.work") },
    { value: "evening", label: t("occasions.evening") },
    { value: "beach", label: t("occasions.beach") },
  ];

  const moods = [
    { value: "classique", label: t("moods.classic") },
    { value: "tendance", label: t("moods.trendy") },
    { value: "decontracte", label: t("moods.relaxed") },
  ];

  return (
    <div className="container mx-auto px-4 py-8 max-w-4xl">
      <h1 className="text-3xl font-bold mb-8">{t("title")}</h1>

      {/* Controls */}
      <div className="space-y-4 mb-8">
        <div>
          <p className="text-sm font-medium mb-2">{t("occasion")}</p>
          <div className="flex flex-wrap gap-2">
            {occasions.map((o) => (
              <Button
                key={o.value}
                variant={occasion === o.value ? "default" : "outline"}
                size="sm"
                onClick={() =>
                  setOccasion(occasion === o.value ? "" : o.value)
                }
              >
                {o.label}
              </Button>
            ))}
          </div>
        </div>

        <div>
          <p className="text-sm font-medium mb-2">{t("mood")}</p>
          <div className="flex flex-wrap gap-2">
            {moods.map((m) => (
              <Button
                key={m.value}
                variant={mood === m.value ? "default" : "outline"}
                size="sm"
                onClick={() => setMood(mood === m.value ? "" : m.value)}
              >
                {m.label}
              </Button>
            ))}
          </div>
        </div>

        <Button onClick={generate} disabled={loading} size="lg" className="mt-4">
          {loading ? t("generating") : t("generate")}
        </Button>
      </div>

      {error && (
        <p className="text-destructive mb-4">{error}</p>
      )}

      {/* Loading skeleton */}
      {loading && (
        <div className="grid gap-4">
          {[1, 2, 3].map((i) => (
            <Card key={i}>
              <CardContent className="flex gap-4 p-4">
                <Skeleton className="w-24 h-32 rounded" />
                <div className="flex-1 space-y-2">
                  <Skeleton className="h-5 w-3/4" />
                  <Skeleton className="h-4 w-1/2" />
                  <Skeleton className="h-4 w-full" />
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Context info */}
      {result && result.context.weather && (
        <div className="mb-6 flex flex-wrap gap-2 text-sm text-muted-foreground">
          <Badge variant="outline">
            {result.context.weather.temperature_c}°C
          </Badge>
          <Badge variant="outline">{result.context.weather.season}</Badge>
          {result.context.trends?.slice(0, 5).map((t) => (
            <Badge key={t} variant="secondary">
              {t}
            </Badge>
          ))}
        </div>
      )}

      {/* Results */}
      {result && !loading && (
        <div className="grid gap-4">
          {result.recommendations.length === 0 ? (
            <p className="text-muted-foreground py-8 text-center">
              {t("empty")}
            </p>
          ) : (
            result.recommendations.map((rec) => (
              <RecommendationCard key={rec.id} rec={rec} />
            ))
          )}
        </div>
      )}
    </div>
  );
}

function RecommendationCard({ rec }: { rec: RecommendationItem }) {
  const t = useTranslations("recommendations");
  const p = rec.product;

  return (
    <Card className="overflow-hidden">
      <CardContent className="flex gap-4 p-4">
        <Link
          href={{ pathname: "/products/[slug]" as const, params: { slug: p.slug } }}
          className="shrink-0"
        >
          <div className="relative w-24 h-32 bg-muted rounded overflow-hidden">
            {p.image_urls[0] && (
              <Image
                src={p.image_urls[0]}
                alt={p.title}
                fill
                className="object-cover"
                sizes="96px"
              />
            )}
          </div>
        </Link>
        <div className="flex-1 min-w-0">
          <div className="flex items-start justify-between gap-2">
            <div>
              {p.brand && (
                <p className="text-xs text-muted-foreground">{p.brand}</p>
              )}
              <Link href={{ pathname: "/products/[slug]" as const, params: { slug: p.slug } }}>
                <h3 className="font-medium line-clamp-2">{p.title}</h3>
              </Link>
            </div>
            <Badge className="shrink-0">
              {Math.round(rec.score * 100)}%
            </Badge>
          </div>
          <p className="text-lg font-bold mt-1">
            {formatPrice(p.price_cents, p.currency)}
          </p>
          {rec.reason && (
            <div className="mt-2 text-sm text-muted-foreground">
              <span className="font-medium">{t("why")}:</span> {rec.reason}
            </div>
          )}
          <div className="mt-2 flex flex-wrap gap-1">
            {p.tags.slice(0, 5).map((tag) => (
              <Badge key={tag} variant="outline" className="text-xs">
                {tag}
              </Badge>
            ))}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
