import type { NextConfig } from "next";
import createNextIntlPlugin from "next-intl/plugin";

const withNextIntl = createNextIntlPlugin("./src/i18n/request.ts");

const nextConfig: NextConfig = {
  images: {
    remotePatterns: [
      { hostname: "img01.ztat.net" },
      { hostname: "images.asos-media.com" },
      { hostname: "static.zara.net" },
      { hostname: "image.hm.com" },
      { hostname: "lp2.hm.com" },
    ],
  },
};

export default withNextIntl(nextConfig);
