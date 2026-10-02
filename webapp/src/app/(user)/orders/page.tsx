"use client";
import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { useState } from "react";
import { Card, Chips, Empty, Skeleton, StatusBadge } from "@/components/ui";
import { PageHeader } from "@/components/Shell";
import { api, type Order } from "@/lib/api";
import { num, usd, when } from "@/lib/format";
import { useT } from "@/lib/i18n";

export default function OrdersPage() {
  const { t } = useT();
  const [f, setF] = useState("all");
  const q = useQuery({ queryKey: ["orders", f], queryFn: () => api.get<{ items: Order[] }>(`/orders?limit=50${f === "all" ? "" : `&status=${f}`}`) });
  return (
    <div className="space-y-4">
      <PageHeader title={t("orders")} />
      <Chips value={f} onChange={setF} options={[{ value: "all", label: t("f_all") }, { value: "active", label: t("f_active") }, { value: "completed", label: t("f_completed") }, { value: "failed", label: t("f_failed") }]} />
      {q.isLoading && <div className="space-y-2"><Skeleton className="h-16" /><Skeleton className="h-16" /></div>}
      {q.data?.items.length === 0 && <Empty text={t("no_orders")} />}
      <div className="space-y-2">
        {q.data?.items.map((o) => (
          <Link key={o.public_id} href={o.status === "awaiting_payment" ? `/checkout/${o.public_id}` : `/orders/${o.public_id}`} data-testid="order-row">
            <Card className="mb-2 flex items-center justify-between gap-3">
              <div className="min-w-0">
                <div className="font-semibold">{o.product_type === "premium" ? `💎 ${t("months", { n: o.plan_months! })}` : `⭐ ${num(o.stars_amount!)}`} <span className="text-hint">→ {o.recipient_type === "self" ? t("for_me") : `@${o.recipient_username}`}</span></div>
                <div className="text-xs text-hint">{o.public_id} · {when(o.created_at)}</div>
              </div>
              <div className="space-y-1 text-right"><StatusBadge status={o.status} /><div className="num text-sm font-semibold">{usd(o.price_usd)}</div></div>
            </Card>
          </Link>
        ))}
      </div>
    </div>
  );
}
