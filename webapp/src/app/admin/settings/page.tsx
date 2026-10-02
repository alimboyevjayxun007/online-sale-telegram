"use client";
import { useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { Btn, Card, ConfirmDialog, Field, Section, inputCls, useToast } from "@/components/ui";
import { PageHeader } from "@/components/Shell";
import { KV, Loading, useAdminGet } from "@/components/admin/parts";
import { useMe } from "@/hooks/queries";
import { api, ApiError } from "@/lib/api";

type S = Record<string, unknown>;
const TOGGLES: [string, string][] = [["payments.ton.enabled", "💎 TON to'lovi"], ["payments.stars.enabled", "⭐ Stars to'lovi"], ["payments.balance.enabled", "💼 Balansdan to'lov"], ["payments.topup.stars.enabled", "➕ Stars bilan balans to'ldirish"], ["referral.enabled", "🤝 Referal tizimi"], ["bot.mandatory_subscription", "📢 Majburiy obuna"], ["fulfillment.auto_refund", "↩️ Avtomatik pul qaytarish"]];

function Switch({ on, onChange, label, testid }: { on: boolean; onChange: (v: boolean) => void; label: string; testid?: string }) {
  return (
    <button onClick={() => onChange(!on)} className="flex w-full items-center justify-between px-4 py-3" data-testid={testid}>
      <span>{label}</span>
      <span className={`relative h-6 w-11 rounded-full transition ${on ? "bg-success" : "bg-line"}`}><span className={`absolute top-0.5 h-5 w-5 rounded-full bg-white shadow transition-all ${on ? "left-[22px]" : "left-0.5"}`} /></span>
    </button>
  );
}

export default function Settings() {
  const qc = useQueryClient();
  const push = useToast((s) => s.push);
  const role = useMe().data?.role;
  const s = useAdminGet<S>("/settings");
  const health = useAdminGet<S>("/health", true, 15000);
  const channels = useAdminGet<{ id: number; chat_id: number; title: string }[]>("/channels");
  const [vals, setVals] = useState<Record<string, string>>({});
  const [cookies, setCookies] = useState("");
  const [maint, setMaint] = useState(false);
  const reload = () => qc.invalidateQueries({ queryKey: ["admin"] });
  const save = async (values: Record<string, unknown>) => {
    try { await api.put("/admin/settings", { values }); push("✅ Saqlandi"); reload(); } catch (e) { push(e instanceof ApiError ? e.message : "Xato", "err"); }
  };
  if (!s.data) return <Loading />;
  const d = s.data;
  const field = (key: string, label: string) => (
    <Field key={key} label={label}>
      <div className="flex gap-2"><input className={inputCls} value={vals[key] ?? String(d[key] ?? "")} onChange={(e) => setVals({ ...vals, [key]: e.target.value })} /><Btn tone="soft" onClick={() => save({ [key]: vals[key] ?? String(d[key] ?? "") })}>💾</Btn></div>
    </Field>
  );
  return (
    <div className="space-y-4">
      <PageHeader title="Sozlamalar" />
      <Card className={`flex items-center justify-between ${d["bot.maintenance"] ? "!bg-warning/15" : ""}`}>
        <div><b>🛠 Texnik ishlar rejimi</b><div className="text-xs text-hint">Oddiy foydalanuvchilar uchun bot va ilova yopiladi</div></div>
        <Btn tone={d["bot.maintenance"] ? "success" : "danger"} onClick={() => setMaint(true)} data-testid="maint-btn">{d["bot.maintenance"] ? "O'chirish" : "Yoqish"}</Btn>
      </Card>
      <Section title="Yoqish / o'chirish">
        <Card className="divide-y divide-line !p-0">{TOGGLES.map(([k, l]) => <Switch key={k} on={Boolean(d[k])} label={l} onChange={(v) => save({ [k]: v })} testid={`toggle-${k}`} />)}</Card>
      </Section>
      <Section title="Qiymatlar">
        <Card className="space-y-3">
          {field("bot.support_username", "Support username (@siz)")}
          {field("referral.percent", "Referal %")}
          {field("payments.invoice_ttl_minutes", "Invoice muddati (daqiqa)")}
          {field("hot_wallet.reserve_ton", "Hot wallet rezerv (TON)")}
          {field("hot_wallet.low_balance_alert_ton", "Past balans ogohlantirishi (TON)")}
          {field("hot_wallet.daily_withdraw_limit_ton", "Kunlik yechish limiti (TON)")}
          {field("notify.log_chat_id", "Log chat ID")}
        </Card>
      </Section>
      {role === "owner" && (
        <Section title="🔐 Fragment">
          <Card className="space-y-3">
            <KV k="Cookie" v={d["fragment.cookies"] ? "✅ kiritilgan" : "— yo'q"} />
            <textarea className={`${inputCls} h-24 py-2 font-mono text-xs`} placeholder="stel_ssid=...; stel_dt=...; stel_token=...; stel_ton_token=..." value={cookies} onChange={(e) => setCookies(e.target.value)} />
            <Btn tone="success" full disabled={!cookies} onClick={async () => { await api.put("/admin/settings/fragment-cookies", { cookies }); setCookies(""); push("✅ Saqlandi (shifrlangan)"); reload(); }}>🔑 Cookie yangilash</Btn>
          </Card>
        </Section>
      )}
      <Section title="📢 Majburiy obuna kanallari">
        <Card className="divide-y divide-line !p-0">
          {channels.data?.length ? channels.data.map((c) => <div key={c.id} className="flex items-center justify-between px-4 py-3"><span>{c.title} <span className="text-xs text-hint">{c.chat_id}</span></span><Btn tone="danger" className="!h-8 !px-3" onClick={async () => { await api.del(`/admin/channels/${c.id}`); reload(); }}>🗑</Btn></div>) : <div className="p-4 text-center text-hint">Kanal yo&apos;q — tekshiruv o&apos;tkazib yuboriladi. Kanalni botdagi ⚙️ Sozlamalar › 📢 orqali qo&apos;shing.</div>}
        </Card>
      </Section>
      <Section title="🩺 Tizim holati">
        <Card>
          <KV k="Baza" v={health.data?.db ? "✅" : "❌"} />
          <KV k="Redis" v={health.data?.redis ? "✅" : "❌"} />
          <KV k="Worker" v={health.data?.worker_heartbeat ? `✅ ${String(health.data.worker_heartbeat).slice(11, 19)}` : "❌"} />
        </Card>
      </Section>
      <ConfirmDialog open={maint} onClose={() => setMaint(false)} title="Texnik ishlar rejimini almashtirasizmi?" confirmLabel="Tasdiqlash" onConfirm={() => save({ "bot.maintenance": !d["bot.maintenance"] })} />
    </div>
  );
}
