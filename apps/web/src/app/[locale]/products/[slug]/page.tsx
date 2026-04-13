import Image from "next/image";
import { notFound } from "next/navigation";
import { useTranslations } from "next-intl";
import { Badge } from "@/components/ui/badge";
import { buttonVariants } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { cn } from "@/lib/utils";
import { ProductCard } from "@/components/product/product-card";
import { getProduct, getSimilarProducts, formatPrice } from "@/lib/api";

export default async function ProductDetailPage({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;
  const product = await getProduct(slug).catch(() => null);
  if (!product) notFound();

  const similar = await getSimilarProducts(product.id).catch(() => []);

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="grid md:grid-cols-2 gap-8">
        {/* Image */}
        <div className="relative aspect-[3/4] bg-muted rounded-lg overflow-hidden">
          {product.image_urls[0] ? (
            <Image
              src={product.image_urls[0]}
              alt={product.title}
              fill
              className="object-cover"
              sizes="(max-width: 768px) 100vw, 50vw"
              priority
            />
          ) : (
            <div className="flex h-full items-center justify-center text-muted-foreground">
              No image
            </div>
          )}
        </div>

        {/* Info */}
        <div className="flex flex-col gap-4">
          {product.brand && (
            <Badge variant="secondary" className="w-fit">
              {product.brand}
            </Badge>
          )}
          <h1 className="text-2xl md:text-3xl font-bold">{product.title}</h1>

          <p className="text-3xl font-bold text-primary">
            {formatPrice(product.price_cents, product.currency)}
          </p>

          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Badge variant="outline" className="capitalize">
              {product.source}
            </Badge>
            {product.subcategory && (
              <Badge variant="outline">{product.subcategory}</Badge>
            )}
          </div>

          <Separator />

          {/* Tags */}
          {product.tags.length > 0 && (
            <div>
              <ProductTags tags={product.tags} />
            </div>
          )}

          {/* CTA */}
          <ViewOnSiteButton url={product.affiliate_url || product.original_url} />

          {product.description && (
            <p className="text-muted-foreground">{product.description}</p>
          )}
        </div>
      </div>

      {/* Similar products */}
      {similar.length > 0 && (
        <section className="mt-16">
          <SimilarSection similar={similar} />
        </section>
      )}
    </div>
  );
}

function ProductTags({ tags }: { tags: string[] }) {
  const t = useTranslations("product");
  return (
    <div>
      <p className="text-sm font-medium mb-2">{t("tags")}</p>
      <div className="flex flex-wrap gap-1.5">
        {tags.map((tag) => (
          <Badge key={tag} variant="secondary" className="text-xs">
            {tag}
          </Badge>
        ))}
      </div>
    </div>
  );
}

function ViewOnSiteButton({ url }: { url: string }) {
  const t = useTranslations("product");
  return (
    <a
      href={url}
      target="_blank"
      rel="noopener noreferrer"
      className={cn(buttonVariants({ size: "lg" }), "w-full md:w-auto")}
    >
      {t("viewOnSite")} &rarr;
    </a>
  );
}

function SimilarSection({ similar }: { similar: { product: import("@/lib/api").Product; score: number }[] }) {
  const t = useTranslations("product");
  return (
    <>
      <h2 className="text-2xl font-bold mb-6">{t("similar")}</h2>
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
        {similar.map((s) => (
          <ProductCard key={s.product.id} product={s.product} />
        ))}
      </div>
    </>
  );
}
