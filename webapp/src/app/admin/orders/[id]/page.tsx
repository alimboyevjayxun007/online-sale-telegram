"use client";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useState } from "react";
import { Btn, Card, ConfirmDialog, ErrorBox, StatusBadge, useToast } from "@/components/ui";
import { PageHeader } from "@/components/Shell";
import { KV, Loading } from "@/components/admin/parts";
import { useMe } from "@/hooks/queries";
import { api, ApiError, type OrderStatus } from "@/lib/api";
import { usd, when } from "@/lib/format";

interface Detail {
  public_id: string; status: OrderStatus; product_type: string; plan_months: number | null; stars_amount: number | null; recipient_username: string | null;
  price_usd: string; payment_method: string; user: { id: number; username: string | null; name: string | null }; cost_usd: string | null; profit_usd: string | null;
  provider: string | null; provider_ref: string | null; error_code: string | null; error_message: string | null; attempts: number;
  events: { from: string | null; to: string; actor: string; at: string }[]; payments: { public_id: string; method: string; status: string; amount: string; currency: string; tx_hash: string | null }[];
}

export default function AdminOrder() {
  const { id } = useParams<{ id: string }>();
  const qc = useQueryClient();
  const push = useToast((s) => s.push);
  const role = useMe().data?.role;
  const q = useQuery({ queryKey: ["admin-order", id], queryFn: () => api.get<Detail>(`/admin/orders/${id}`) });
  const [confirm, setConfirm] = useState<null | "retry" | "refund" | "complete">(null);
  if (q.error) return <ErrorBox error={q.error} onRetry={() => q.refetch()} />;
  if (!q.data) return <Loading />;
  const o = q.data;
  const act = async (kind: "retry" | "refund" | "complete") => {
    try {
      await api.post(`/admin/orders/${id}/${kind === "complete" ? "mark-completed" : kind}`, kind === "refund" ? { to: "auto" } : {});
      push("✅ OK");
      qc.invalidateQueries({ queryKey: ["admin-order", id] });
    } catch (e) { push(e instanceof ApiError ? e.message : "Xato", "err"); }
  };
  const fixable = o.status === "needs_review" || o.status === "failed";
  const labels = { retry: "🔄 Qayta urinish", refund: "↩️ Pulni qaytarish", complete: "✅ Qo'lda bajarildi" };
  return (
    <div className="space-y-4">
      <PageHeader title={o.public_id} right={<StatusBadge status={o.status} />} />
      <Card>
        <KV k="Mahsulot" v={o.product_type === "premium" ? `💎 Premium ${o.plan_months} oy` : `⭐ Stars ${o.stars_amount}`} />
        <KV k="Qabul qiluvchi" v={o.recipient_username ? `@${o.recipient_username}` : "o'zi"} />
        <KV k="Xaridor" v={<Link href={`/admin/users/${o.user.id}`} className="text-accent">{o.user.name} @{o.user.username ?? "-"}</Link>} />
        <KV k="Narx" v={`${usd(o.price_usd)} · ${o.payment_method}`} />
        {o.cost_usd && <KV k="Tannarx / foyda" v={`${usd(o.cost_usd)} / ${usd(o.profit_usd ?? 0)}`} />}
        <KV k="Provider" v={`${o.provider ?? "—"} · urinish ${o.attempts}`} />
        {o.error_code && <KV k="Xato" v={`${o.error_code} ${o.error_message ?? ""}`} />}
        {o.provider_ref && o.provider_ref.length === 64 && <KV k="Tx" v={<a className="text-accent" href={`https://tonviewer.com/transaction/${o.provider_ref}`} target="_blank">tonviewer</a>} />}
      </Card>
      {(fixable || o.status === "paid") && (
        <div className="space-y-2">
          {fixable && role !== "support" && <Btn tone="success" full onClick={() => setConfirm("complete")}>{labels.complete}</Btn>}
          {fixable && <Btn tone="primary" full onClick={() => setConfirm("retry")}>{labels.retry}</Btn>}
          {role !== "support" && <Btn tone="danger" full onClick={() => setConfirm("refund")}>{labels.refund}</Btn>}
        </div>
      )}
      <Card className="space-y-1.5 text-sm">
        <div className="font-semibold">Holat tarixi</div>
        {o.events.map((e, i) => <div key={i} className="flex justify-between"><span>{e.from ?? "·"} → <b>{e.to}</b> <span className="text-hint">({e.actor})</span></span><span className="text-hint">{when(e.at)}</span></div>)}
      </Card>
      <Card className="space-y-1.5 text-sm">
        <div className="font-semibold">To&apos;lovlar</div>
        {o.payments.map((p) => <div key={p.public_id} className="flex justify-between"><span>{p.public_id} · {p.method}</span><span className="num">{p.amount} {p.currency} · {p.status}</span></div>)}
      </Card>
      <ConfirmDialog open={!!confirm} onClose={() => setConfirm(null)} title={confirm ? `${labels[confirm]}?` : ""} text={o.public_id} danger={confirm === "refund"} onConfirm={() => confirm && act(confirm)} confirmLabel="Tasdiqlash" />
    </div>
  );
}
