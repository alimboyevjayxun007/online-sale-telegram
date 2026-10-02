"use client";
import { useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { Btn, Card, ConfirmDialog, Field, Section, inputCls, useToast } from "@/components/ui";
import { PageHeader } from "@/components/Shell";
import { KV, Loading, useAdminGet } from "@/components/admin/parts";
import { useMe } from "@/hooks/queries";
import { api, ApiError } from "@/lib/api";
import { ton, usd, when } from "@/lib/format";

interface Overview { admin_address: string; hot_wallet_address: string; hot_wallet_ton: string | null; withdrawable_ton?: string; liabilities_usd: string; stars_ledger: number; unmatched_pending: number; frozen: boolean; sweep_enabled: boolean }
const CATS = ["server", "domain", "fragment_fee", "network_fee", "advertising", "salary", "other"];

export default function Finance() {
  const qc = useQueryClient();
  const push = useToast((s) => s.push);
  const role = useMe().data?.role;
  const o = useAdminGet<Overview>("/finance/overview");
  const hw = useAdminGet<{ direction: string; kind: string; amount_ton: string; at: string; tx_hash: string | null }[]>("/finance/hot-wallet/transactions?limit=10");
  const um = useAdminGet<{ id: number; amount_ton: string; comment: string | null; sender: string | null }[]>("/finance/unmatched");
  const ex = useAdminGet<{ id: number; category: string; amount_usd: string; note: string | null; spent_on: string }[]>("/expenses");
  const [amount, setAmount] = useState("");
  const [confirm, setConfirm] = useState(false);
  const [exp, setExp] = useState({ category: "server", amount: "", note: "" });
  const reload = () => qc.invalidateQueries({ queryKey: ["admin"] });
  if (!o.data) return <Loading />;
  const d = o.data;
  const withdraw = async () => {
    try { const r = await api.post<{ tx_hash: string }>("/admin/finance/withdraw", { amount_ton: amount }); push(`✅ ${r.tx_hash.slice(0, 10)}…`); setAmount(""); reload(); }
    catch (e) { push(e instanceof ApiError ? e.message : "Xato", "err"); }
  };
  const addExpense = async () => {
    try { await api.post("/admin/expenses", { category: exp.category, amount_usd: exp.amount, note: exp.note || null }); push("✅ Saqlandi"); setExp({ ...exp, amount: "", note: "" }); reload(); }
    catch (e) { push(e instanceof ApiError ? e.message : "Xato", "err"); }
  };
  const resolve = async (id: number, user?: string) => {
    try { await api.post(`/admin/finance/unmatched/${id}/resolve`, user ? { user_id: Number(user) } : {}); reload(); } catch (e) { push(e instanceof ApiError ? e.message : "Xato", "err"); }
  };
  return (
    <div className="space-y-4">
      <PageHeader title="Moliya" />
      <Card>
        <KV k="💎 Hot wallet" v={d.hot_wallet_ton ? `${ton(d.hot_wallet_ton)} TON` : "—"} />
        <KV k="Yechish mumkin" v={d.withdrawable_ton ? `${ton(d.withdrawable_ton)} TON` : "—"} />
        <KV k="⭐ Stars (ledger)" v={d.stars_ledger} />
        <KV k="💼 Foydalanuvchi balanslari" v={usd(d.liabilities_usd)} />
        <KV k="🏦 Admin hamyon" v={<span className="break-all font-mono text-xs">{d.admin_address || "—"}</span>} />
        <KV k="Holat" v={`${d.frozen ? "🧊 muzlatilgan" : "faol"} · avto-o'tkazish ${d.sweep_enabled ? "✅" : "⛔️"}`} />
      </Card>
      {role === "owner" && (
        <Card className="space-y-2">
          <div className="font-semibold">💸 Telegram Wallet&apos;ga yechish</div>
          <div className="text-xs text-hint">Faqat .env dagi admin manzilga yuboriladi.</div>
          <div className="flex gap-2"><input className={inputCls} inputMode="decimal" placeholder="TON" value={amount} onChange={(e) => setAmount(e.target.value)} data-testid="withdraw-amount" /><Btn tone="success" disabled={!amount} onClick={() => setConfirm(true)}>Yechish</Btn></div>
        </Card>
      )}
      <Section title={`❓ Mos kelmagan to'lovlar (${um.data?.length ?? 0})`}>
        <Card className="divide-y divide-line !p-0">
          {um.data?.length ? um.data.map((r) => <UnmatchedRow key={r.id} r={r} onResolve={resolve} />) : <div className="p-4 text-center text-hint">Yo&apos;q</div>}
        </Card>
      </Section>
      <Section title="🧾 Xarajatlar">
        <Card className="space-y-2">
          <div className="grid grid-cols-2 gap-2">
            <Field label="Kategoriya"><select className={inputCls} value={exp.category} onChange={(e) => setExp({ ...exp, category: e.target.value })}>{CATS.map((c) => <option key={c}>{c}</option>)}</select></Field>
            <Field label="Summa ($)"><input className={inputCls} inputMode="decimal" value={exp.amount} onChange={(e) => setExp({ ...exp, amount: e.target.value })} data-testid="expense-amount" /></Field>
          </div>
          <input className={inputCls} placeholder="Izoh" value={exp.note} onChange={(e) => setExp({ ...exp, note: e.target.value })} />
          <Btn tone="primary" full disabled={!exp.amount} onClick={addExpense} data-testid="expense-save">➕ Qo&apos;shish</Btn>
        </Card>
        <Card className="divide-y divide-line !p-0">
          {ex.data?.slice(0, 8).map((e) => <div key={e.id} className="flex justify-between px-4 py-2.5 text-sm"><span>{e.spent_on} · {e.category} {e.note ?? ""}</span><b className="num">{usd(e.amount_usd)}</b></div>)}
        </Card>
      </Section>
      <Section title="📜 Hot wallet harakati">
        <Card className="divide-y divide-line !p-0">
          {hw.data?.length ? hw.data.map((r, i) => <div key={i} className="flex justify-between px-4 py-2.5 text-sm"><span>{r.direction === "in" ? "⬇️" : "⬆️"} {r.kind}</span><span className="num">{ton(r.amount_ton)} TON <span className="text-xs text-hint">{when(r.at)}</span></span></div>) : <div className="p-4 text-center text-hint">Bo&apos;sh</div>}
        </Card>
      </Section>
      <ConfirmDialog open={confirm} onClose={() => setConfirm(false)} title={`${amount} TON yechilsinmi?`} text={d.admin_address} confirmLabel="Tasdiqlash" onConfirm={withdraw} />
    </div>
  );
}

function UnmatchedRow({ r, onResolve }: { r: { id: number; amount_ton: string; comment: string | null; sender: string | null }; onResolve: (id: number, user?: string) => void }) {
  const [uid, setUid] = useState("");
  return (
    <div className="space-y-2 px-4 py-3 text-sm">
      <div className="flex justify-between"><b className="num">{ton(r.amount_ton)} TON</b><span className="text-hint">izoh: {r.comment || "—"}</span></div>
      <div className="flex gap-2"><input className={inputCls} placeholder="User ID (balansga)" value={uid} onChange={(e) => setUid(e.target.value)} /><Btn tone="success" disabled={!uid} onClick={() => onResolve(r.id, uid)}>✓</Btn><Btn tone="soft" onClick={() => onResolve(r.id)}>Ignore</Btn></div>
    </div>
  );
}
