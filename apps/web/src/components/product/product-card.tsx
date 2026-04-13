import Image from "next/image";
import { Link } from "@/i18n/navigation";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { type Product, formatPrice } from "@/lib/api";

export function ProductCard({
  product,
  locale = "fr-FR",
}: {
  product: Product;
  locale?: string;
}) {
  const imageUrl = product.image_urls[0];

  return (
    <Link href={{ pathname: "/products/[slug]" as const, params: { slug: product.slug } }}>
      <Card className="group overflow-hidden transition-shadow hover:shadow-lg">
        <div className="relative aspect-[3/4] bg-muted">
          {imageUrl ? (
            <Image
              src={imageUrl}
              alt={product.title}
              fill
              className="object-cover transition-transform group-hover:scale-105"
              sizes="(max-width: 640px) 50vw, (max-width: 1024px) 33vw, 25vw"
            />
          ) : (
            <div className="flex h-full items-center justify-center text-muted-foreground">
              No image
            </div>
          )}
          {product.brand && (
            <Badge
              variant="secondary"
              className="absolute top-2 left-2 text-xs"
            >
              {product.brand}
            </Badge>
          )}
        </div>
        <CardContent className="p-3">
          <p className="text-sm font-medium line-clamp-2 leading-tight">
            {product.title}
          </p>
          <div className="mt-2 flex items-center justify-between">
            <span className="text-base font-bold">
              {formatPrice(product.price_cents, product.currency, locale)}
            </span>
            <Badge variant="outline" className="text-xs capitalize">
              {product.source}
            </Badge>
          </div>
        </CardContent>
      </Card>
    </Link>
  );
}
