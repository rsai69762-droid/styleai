import type { Metadata } from "next";
import { Geist } from "next/font/google";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: {
    template: "%s | StylAI",
    default: "StylAI - Mode personnalisée par IA",
  },
  description:
    "Recommandations mode personnalisées par intelligence artificielle",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return children;
}
