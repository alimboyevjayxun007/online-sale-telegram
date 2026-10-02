"use client";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useParams } from "next/navigation";
import { useState } from "react";
import Link from "next/link";
import { Btn, Card, ConfirmDialog, ErrorBox, Modal, StatusBadge, inputCls, useToast } from "@/components/ui";
import { PageHeader } from "@/components/Shell";
import { KV, Loading } from "@/components/admin/parts";
import { useMe } from "@/hooks/queries";
import { api, ApiError, type Order } from "@/lib/api";
import { usd, when } from "@/lib/format";

interface Detail {
  id: number; username: string | null; name: string | null; language: string; balance_usd: string; total_spent_usd: string; orders_count: number; is_banned: boolean;
  ban_reason: string | null; created_at: string; last_seen_at: string; source: string | null; referrer_id: number | null; invited: number;
  orders: Order[]; ledger: { amount_usd: string; type: string; at: string }[];
}

export default function AdminUser() {
  const { id } = useParams<{ id: string }>();
  const qc = useQueryClient();
  const push = useToast((s) => s.push);
  const role = useMe().data?.role;
  const q = useQuery({ queryKey: ["admin-user", id], queryFn: () => api.get<Detail>(`/admin/users/${id}`) });
  const [modal, setModal] = useState<null | "balance" | "message">(null);
  const [ban, setBan] = useState(false);
  const [amount, setAmount] = useState("");
  const [text, setText] = useState("");
  if (q.error) return <ErrorBox error={q.error} onRetry={() => q.refetch()} />;
  if (!q.data) return <Loading />;
  const u = q.data;
  const run = async (fn: () => Promise<unknown>) => {
    try { await fn(); push("✅ OK"); qc.invalidateQueries({ queryKey: ["admin-user", id] }); setModal(null); }
    catch (e) { push(e instanceof ApiError ? e.message : "Xato", "err"); }
  };
  return (
    <div className="space-y-4">
      <PageHeader title={`${u.name ?? ""} ${u.is_banned ? "⛔️" : ""}`} />
      <Card>
        <KV k="ID / username" v={`${u.id} · @${u.username ?? "-"}`} />
        <KV k="Balans" v={usd(u.balance_usd)} />
        <KV k="Buyurtmalar / xarid" v={`${u.orders_count} · ${usd(u.total_spent_usd)}`} />
        <KV k="Taklif qilgan / taklif qilgan odam" v={`${u.invited} / ${u.referrer_id ?? "—"}`} />
        <KV k="Ro'yxatdan o'tgan" v={when(u.created_at)} />
        <KV k="Oxirgi faollik" v={when(u.last_seen_at)} />
        <KV k="Manba / til" v={`${u.source ?? "—"} · ${u.language}`} />
        {u.is_banned && <KV k="Ban sababi" v={u.ban_reason ?? "—"} />}
      </Card>
      <div className="grid grid-cols-2 gap-2">
        {role !== "support" && <Btn tone="success" onClick={() => setModal("balance")}>💼 Balans ±</Btn>}
        <Btn tone="primary" onClick={() => setModal("message")}>✉️ Xabar</Btn>
        {role !== "support" && <Btn tone={u.is_banned ? "success" : "danger"} className="col-span-2" onClick={() => setBan(true)}>{u.is_banned ? "✅ Blokdan chiqarish" : "⛔️ Bloklash"}</Btn>}
      </div>
      <Card className="space-y-1.5 text-sm">
        <div className="font-semibold">Buyurtmalar</div>
        {u.orders.map((o) => <Link key={o.public_id} href={`/admin/orders/${o.public_id}`} className="flex justify-between"><span>{o.public_id}</span><span className="flex items-center gap-2"><StatusBadge status={o.status} /><span className="num">{usd(o.price_usd)}</span></span></Link>)}
      </Card>
      <Card className="space-y-1.5 text-sm">
        <div className="font-semibold">Balans tarixi</div>
        {u.ledger.map((l, i) => <div key={i} className="flex justify-between"><span>{l.type}</span><span className={`num ${Number(l.amount_usd) > 0 ? "text-success" : "text-danger"}`}>{usd(l.amount_usd)} <span className="text-hint">{when(l.at)}</span></span></div>)}
      </Card>
      <Modal open={modal === "balance"} onClose={() => setModal(null)} title="Balansni o'zgartirish">
        <input className={inputCls} inputMode="decimal" placeholder="+5 yoki -2.5 ($)" value={amount} onChange={(e) => setAmount(e.target.value)} data-testid="balance-amount" />
        <Btn tone="success" full onClick={() => run(() => api.post(`/admin/users/${id}/balance`, { amount_usd: amount, comment: "admin" }))}>Saqlash</Btn>
      </Modal>
      <Modal open={modal === "message"} onClose={() => setModal(null)} title="Xabar yuborish">
        <textarea className={`${inputCls} h-28 py-2`} value={text} onChange={(e) => setText(e.target.value)} />
        <Btn tone="primary" full disabled={!text} onClick={() => run(() => api.post(`/admin/users/${id}/message`, { text }))}>Yuborish</Btn>
      </Modal>
      <ConfirmDialog open={ban} onClose={() => setBan(false)} title={u.is_banned ? "Blokdan chiqarilsinmi?" : "Bloklansinmi?"} danger={!u.is_banned} confirmLabel="Tasdiqlash"
        onConfirm={() => run(() => api.post(`/admin/users/${id}/${u.is_banned ? "unban" : "ban"}`, {}))} />
    </div>
  );
}
