"use client";
import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Suspense, useState } from "react";
import { Card, Chips, Empty, StatusBadge, inputCls } from "@/components/ui";
import { PageHeader } from "@/components/Shell";
import { Loading } from "@/components/admin/parts";
import { api, type Order } from "@/lib/api";
import { usd, when } from "@/lib/format";

type Row = Order & { user_id: number; provider: string | null };
const FILTERS = [["", "Hammasi"], ["needs_review", "🔍 Tekshirish"], ["failed", "❌ Xato"], ["processing", "⚙️ Jarayonda"], ["awaiting_payment", "⏳ Kutilmoqda"], ["completed", "✅ Bajarilgan"]];

function List() {
  const sp = useSearchParams();
  const [status, setStatus] = useState(sp.get("status") ?? "");
  const [q, setQ] = useState("");
  const data = useQuery({ queryKey: ["admin", "orders", status, q], queryFn: () => api.get<{ items: Row[] }>(`/admin/orders?limit=50${status ? `&status=${status}` : ""}${q ? `&q=${encodeURIComponent(q)}` : ""}`) });
  return (
    <div className="space-y-4">
      <PageHeader title="Buyurtmalar" />
      <input className={inputCls} placeholder="🔎 PR-XXXXXX, @username yoki user ID" value={q} onChange={(e) => setQ(e.target.value)} data-testid="order-search" />
      <Chips value={status} onChange={setStatus} options={FILTERS.map(([value, label]) => ({ value, label }))} />
      {data.isLoading && <Loading />}
      {data.data?.items.length === 0 && <Empty text="Buyurtmalar yo'q" />}
      {data.data?.items.map((o) => (
        <Link key={o.public_id} href={`/admin/orders/${o.public_id}`} data-testid="admin-order-row">
          <Card className="mb-2 flex items-center justify-between gap-3">
            <div className="min-w-0">
              <div className="font-semibold">{o.product_type === "premium" ? `💎 ${o.plan_months} oy` : `⭐ ${o.stars_amount}`} <span className="text-hint">→ {o.recipient_username ? `@${o.recipient_username}` : "o'zi"}</span></div>
              <div className="text-xs text-hint">{o.public_id} · user {o.user_id} · {when(o.created_at)}</div>
            </div>
            <div className="space-y-1 text-right"><StatusBadge status={o.status} /><div className="num text-sm font-semibold">{usd(o.price_usd)}</div></div>
          </Card>
        </Link>
      ))}
    </div>
  );
}

export default function AdminOrders() {
  return <Suspense fallback={<Loading />}><List /></Suspense>;
}
