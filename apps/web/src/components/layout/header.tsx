"use client";

import { useTranslations } from "next-intl";
import { Link, usePathname, useRouter } from "@/i18n/navigation";
import {
  Sheet,
  SheetContent,
  SheetTrigger,
  SheetTitle,
} from "@/components/ui/sheet";
import { Button } from "@/components/ui/button";
import { LocaleSwitcher } from "./locale-switcher";
import { useAuth } from "@/components/auth/auth-provider";
import { createClient } from "@/lib/supabase/client";
import { useState } from "react";

export function Header() {
  const t = useTranslations("nav");
  const tAuth = useTranslations("auth");
  const pathname = usePathname();
  const router = useRouter();
  const { session, loading } = useAuth();
  const [open, setOpen] = useState(false);

  const navItems = [
    { href: "/" as const, label: t("home") },
    { href: "/products" as const, label: t("products") },
    { href: "/recommendations" as const, label: t("recommendations") },
  ];

  async function handleLogout() {
    const supabase = createClient();
    await supabase.auth.signOut();
    router.push("/");
    router.refresh();
  }

  return (
    <header className="sticky top-0 z-50 border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="container mx-auto flex h-14 items-center px-4">
        <Link href="/" className="mr-6 flex items-center gap-2 font-bold text-lg">
          <span className="bg-gradient-to-r from-purple-600 to-pink-500 bg-clip-text text-transparent">
            StylAI
          </span>
        </Link>

        {/* Desktop nav */}
        <nav className="hidden md:flex items-center gap-6 text-sm">
          {navItems.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className={`transition-colors hover:text-foreground/80 ${
                pathname === item.href
                  ? "text-foreground font-medium"
                  : "text-foreground/60"
              }`}
            >
              {item.label}
            </Link>
          ))}
        </nav>

        <div className="ml-auto flex items-center gap-2">
          <LocaleSwitcher />

          {!loading && (
            session ? (
              <Button variant="ghost" size="sm" onClick={handleLogout}>
                {tAuth("logout")}
              </Button>
            ) : (
              <Link href="/login">
                <Button variant="default" size="sm">
                  {tAuth("login")}
                </Button>
              </Link>
            )
          )}

          {/* Mobile menu */}
          <Sheet open={open} onOpenChange={setOpen}>
            <SheetTrigger className="md:hidden inline-flex items-center justify-center rounded-lg p-2 hover:bg-muted">
              <svg width="20" height="20" viewBox="0 0 15 15" fill="none">
                <path
                  d="M1.5 3C1.22386 3 1 3.22386 1 3.5C1 3.77614 1.22386 4 1.5 4H13.5C13.7761 4 14 3.77614 14 3.5C14 3.22386 13.7761 3 13.5 3H1.5ZM1 7.5C1 7.22386 1.22386 7 1.5 7H13.5C13.7761 7 14 7.22386 14 7.5C14 7.77614 13.7761 8 13.5 8H1.5C1.22386 8 1 7.77614 1 7.5ZM1 11.5C1 11.2239 1.22386 11 1.5 11H13.5C13.7761 11 14 11.2239 14 11.5C14 11.7761 13.7761 12 13.5 12H1.5C1.22386 12 1 11.7761 1 11.5Z"
                  fill="currentColor"
                />
              </svg>
            </SheetTrigger>
            <SheetContent side="right">
              <SheetTitle>Menu</SheetTitle>
              <nav className="flex flex-col gap-4 mt-6">
                {navItems.map((item) => (
                  <Link
                    key={item.href}
                    href={item.href}
                    onClick={() => setOpen(false)}
                    className="text-lg font-medium"
                  >
                    {item.label}
                  </Link>
                ))}
              </nav>
            </SheetContent>
          </Sheet>
        </div>
      </div>
    </header>
  );
}
