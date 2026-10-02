"use client";
import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { ChevronRight } from "lucide-react";
import { Card, Section, Skeleton, StatusBadge } from "@/components/ui";
import { useCatalog, useMe } from "@/hooks/queries";
import { api, type Order } from "@/lib/api";
import { num, usd, uzs } from "@/lib/format";
import { useT } from "@/lib/i18n";

export default function Home() {
  const { t } = useT();
  const me = useMe();
  const cat = useCatalog();
  const orders = useQuery({ queryKey: ["orders", "recent"], queryFn: () => api.get<{ items: Order[] }>("/orders?limit=3") });
  const m = me.data;
  const plans = cat.data?.plans.filter((p) => p.available) ?? [];
  const cheapest = plans[0];
  const firstPkg = cat.data?.star_packages[0];
  const maxSaving = Math.max(0, ...plans.map((p) => p.saving_pct ?? 0));
  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <h1 className="text-[22px] font-bold" data-testid="hello">{m ? t("hello", { name: m.name ?? "" }) : <Skeleton className="h-7 w-40" />}</h1>
        <span className="rounded-full bg-surface px-2.5 py-1 text-xs font-semibold uppercase text-hint">{m?.language}</span>
      </div>

      <Card className="space-y-3 !bg-[image:var(--premium-gradient)] text-white">
        <div className="text-sm opacity-90">💼 {t("balance")}</div>
        <div className="num text-[32px] font-bold leading-9" data-testid="home-balance">{m ? usd(m.balance_usd) : "—"}</div>
        <div className="flex items-center justify-between">
          <span className="num text-sm opacity-90">{m ? `≈ ${uzs(m.balance_uzs)}` : ""}</span>
          <Link href="/wallet/topup"><span className="rounded-xl bg-white/25 px-4 py-2 text-sm font-semibold">+ {t("topup")}</span></Link>
        </div>
      </Card>

      <div className="grid grid-cols-2 gap-3">
        <Link href="/premium" data-testid="card-premium">
          <div className="h-full space-y-1 rounded-3xl p-4 text-white [background:var(--premium-gradient)]">
            <div className="float text-3xl">💎</div>
            <div className="text-lg font-bold">Premium</div>
            <div className="text-xs opacity-90">3 · 6 · 12 {t("months", { n: "" }).trim()}</div>
            <div className="num text-sm font-semibold">{cheapest ? t("from", { p: usd(cheapest.price_usd!) }) : "…"}</div>
            {maxSaving > 0 && <div className="text-xs">{t("up_to", { p: `${maxSaving}%` })}</div>}
          </div>
        </Link>
        <Link href="/stars" data-testid="card-stars">
          <div className="h-full space-y-1 rounded-3xl p-4 text-black [background:var(--stars-gradient)]">
            <div className="float text-3xl">⭐</div>
            <div className="text-lg font-bold">Stars</div>
            <div className="text-xs opacity-80">{t("min50")}</div>
            <div className="num text-sm font-semibold">{firstPkg ? t("from", { p: usd(firstPkg.price_usd) }) : "…"}</div>
          </div>
        </Link>
      </div>

      <div className="flex justify-around text-center text-xs font-medium text-hint">
        <span>⚡ {t("fast")}</span><span>🔒 {t("official")}</span><span>💬 {t("support247")}</span>
      </div>

      <Section title={t("recent")} action={<Link href="/orders" className="text-sm text-accent">{t("all")} ›</Link>}>
        <Card className="divide-y divide-line !p-0">
          {orders.isLoading && <div className="p-4"><Skeleton /></div>}
          {orders.data?.items.length === 0 && <div className="p-4 text-center text-hint">{t("no_orders")}</div>}
          {orders.data?.items.map((o) => (
            <Link key={o.public_id} href={o.status === "awaiting_payment" ? `/checkout/${o.public_id}` : `/orders/${o.public_id}`} className="flex items-center justify-between gap-2 px-4 py-3">
              <span className="min-w-0 truncate">{o.product_type === "premium" ? `💎 ${t("months", { n: o.plan_months! })}` : `⭐ ${num(o.stars_amount!)}`} → {o.recipient_type === "self" ? t("for_me") : `@${o.recipient_username}`}</span>
              <StatusBadge status={o.status} />
            </Link>
          ))}
        </Card>
      </Section>

      <Link href="/referral">
        <Card className="flex items-center justify-between">
          <div><div className="font-semibold">👥 {t("invite_title")}</div><div className="text-sm text-hint">{t("invite_sub", { p: 2 })}</div></div>
          <ChevronRight className="text-hint" />
        </Card>
      </Link>
    </div>
  );
}
