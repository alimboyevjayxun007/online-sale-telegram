"use client";
import clsx from "clsx";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { BarChart3, Gem, Home, Menu, Package, Star, User, Users, Wallet } from "lucide-react";
import { useT } from "@/lib/i18n";
import { haptic } from "@/lib/tma";

function Bar({ items }: { items: { href: string; label: string; icon: React.ReactNode; match?: string }[] }) {
  const path = usePathname();
  return (
    <nav className="safe-bottom fixed inset-x-0 bottom-0 z-20 border-t border-line bg-bg/95 pt-1.5 backdrop-blur" data-testid="bottom-nav">
      <ul className="mx-auto flex max-w-md justify-between px-2">
        {items.map((i) => {
          const active = i.href === "/" || i.href === "/admin" ? path === i.href : path.startsWith(i.match ?? i.href);
          return (
            <li key={i.href} className="flex-1">
              <Link href={i.href} onClick={() => haptic("select")} className={clsx("flex flex-col items-center gap-0.5 py-1 text-[11px] font-medium", active ? "text-accent" : "text-hint")}>
                {i.icon}
                {i.label}
              </Link>
            </li>
          );
        })}
      </ul>
    </nav>
  );
}

export function BottomNav() {
  const { t } = useT();
  return (
    <Bar items={[
      { href: "/", label: t("nav_home"), icon: <Home size={22} /> },
      { href: "/premium", label: t("premium"), icon: <Gem size={22} /> },
      { href: "/stars", label: t("stars"), icon: <Star size={22} /> },
      { href: "/wallet", label: t("nav_wallet"), icon: <Wallet size={22} /> },
      { href: "/profile", label: t("nav_profile"), icon: <User size={22} /> },
    ]} />
  );
}

export function AdminNav() {
  return (
    <Bar items={[
      { href: "/admin", label: "Dashboard", icon: <BarChart3 size={22} /> },
      { href: "/admin/orders", label: "Buyurtma", icon: <Package size={22} /> },
      { href: "/admin/users", label: "Users", icon: <Users size={22} /> },
      { href: "/admin/finance", label: "Moliya", icon: <Wallet size={22} /> },
      { href: "/admin/more", label: "Ko'proq", icon: <Menu size={22} /> },
    ]} />
  );
}
