"use client";
import { useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { Btn, Card, Field, Section, inputCls, useToast } from "@/components/ui";
import { PageHeader } from "@/components/Shell";
import { Loading, useAdminGet } from "@/components/admin/parts";
import { api, ApiError } from "@/lib/api";

interface Plan { id: number; months: number; is_enabled: boolean; provider_supported: boolean; markup_percent?: string; fixed_price_usd?: string; price_stars?: number; badge?: string; cost_ton?: string; quote: { price_usd: string; cost_usd: string; profit_usd: string; price_ton: string } | null }

function PlanCard({ p, onSaved }: { p: Plan; onSaved: () => void }) {
  const push = useToast((s) => s.push);
  const [markup, setMarkup] = useState(p.markup_percent ?? "8");
  const [fixed, setFixed] = useState(p.fixed_price_usd ?? "");
  const [stars, setStars] = useState(String(p.price_stars ?? ""));
  const [badge, setBadge] = useState(p.badge ?? "");
  const [cost, setCost] = useState(p.cost_ton ? String(Number(p.cost_ton)) : "");
  const save = async (extra: Record<string, unknown> = {}) => {
    try {
      await api.put(`/admin/pricing/plans/${p.id}`, { markup_percent: markup, ...(fixed ? { fixed_price_usd: fixed } : { clear_fixed_price: true }), price_stars: stars ? Number(stars) : undefined, badge: badge || null, ...(cost ? { cost_ton: cost } : {}), ...extra });
      push("✅ Saqlandi");
      onSaved();
    } catch (e) { push(e instanceof ApiError ? e.message : "Xato", "err"); }
  };
  if (!p.provider_supported) return <Card className="opacity-70"><b>💎 {p.months} oy</b> <span className="text-sm text-hint">— Telegram hozircha sovg&apos;a qilishni qo&apos;llamaydi (kulrang &quot;tez kunda&quot;)</span></Card>;
  return (
    <Card className="space-y-3" data-testid={`plan-card-${p.months}`}>
      <div className="flex items-center justify-between">
        <b className="text-lg">💎 {p.months} oy</b>
        <label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={p.is_enabled} onChange={(e) => save({ is_enabled: e.target.checked })} />{p.is_enabled ? "Yoqilgan" : "O'chiq"}</label>
      </div>
      {p.quote ? (
        <div className="grid grid-cols-3 gap-2 text-center text-sm">
          <div><div className="text-xs text-hint">Tannarx</div><b className="num">{Number(p.quote.cost_usd).toFixed(2)} $</b></div>
          <div><div className="text-xs text-hint">Narx</div><b className="num">{Number(p.quote.price_usd).toFixed(2)} $</b></div>
          <div><div className="text-xs text-hint">Foyda</div><b className="num text-success">{Number(p.quote.profit_usd).toFixed(2)} $</b></div>
        </div>
      ) : <div className="text-sm text-warning">Narx noma&apos;lum — tannarxni (TON) kiriting</div>}
      <div className="grid grid-cols-2 gap-2">
        <Field label="Ustama %"><input className={inputCls} value={markup} onChange={(e) => setMarkup(e.target.value)} inputMode="decimal" data-testid={`markup-${p.months}`} /></Field>
        <Field label="Qat'iy narx ($)"><input className={inputCls} value={fixed} onChange={(e) => setFixed(e.target.value)} inputMode="decimal" placeholder="—" /></Field>
        <Field label="Stars narxi"><input className={inputCls} value={stars} onChange={(e) => setStars(e.target.value)} inputMode="numeric" /></Field>
        <Field label="Tannarx (TON)"><input className={inputCls} value={cost} onChange={(e) => setCost(e.target.value)} inputMode="decimal" /></Field>
        <Field label="Belgi"><input className={inputCls} value={badge} onChange={(e) => setBadge(e.target.value)} placeholder="🔥" /></Field>
      </div>
      <Btn tone="success" full onClick={() => save()} data-testid={`save-${p.months}`}>💾 Saqlash</Btn>
    </Card>
  );
}

export default function Pricing() {
  const qc = useQueryClient();
  const push = useToast((s) => s.push);
  const plans = useAdminGet<Plan[]>("/pricing/plans");
  const settings = useAdminGet<Record<string, unknown>>("/settings");
  const [markup, setMarkup] = useState<string | null>(null);
  const reload = () => { qc.invalidateQueries({ queryKey: ["admin", "/pricing/plans"] }); qc.invalidateQueries({ queryKey: ["catalog"] }); };
  if (!plans.data || !settings.data) return <Loading />;
  const sm = markup ?? String(settings.data["pricing.stars.markup_percent"]);
  const saveSetting = async (key: string, value: string) => { try { await api.put("/admin/settings", { values: { [key]: value } }); push("✅ Saqlandi"); reload(); } catch (e) { push(e instanceof ApiError ? e.message : "Xato", "err"); } };
  return (
    <div className="space-y-4">
      <PageHeader title="Narxlar" right={<Btn tone="soft" onClick={async () => { const r = await api.post<{ updated: number }>("/admin/pricing/refresh"); push(`🔄 ${r.updated}`); reload(); }}>🔄 Fragment</Btn>} />
      {plans.data.map((p) => <PlanCard key={`${p.id}-${p.markup_percent}-${p.fixed_price_usd}-${p.is_enabled}`} p={p} onSaved={reload} />)}
      <Section title="⭐ Stars va umumiy">
        <Card className="space-y-3">
          <Field label="Stars ustamasi %"><div className="flex gap-2"><input className={inputCls} value={sm} onChange={(e) => setMarkup(e.target.value)} inputMode="decimal" /><Btn tone="success" onClick={() => saveSetting("pricing.stars.markup_percent", sm)}>💾</Btn></div></Field>
          {[["pricing.min_margin_percent", "Minimal foyda %"], ["pricing.network_fee_ton", "Tarmoq komissiyasi (TON)"], ["pricing.round_step_usd", "Yaxlitlash qadami ($)"]].map(([k, l]) => (
            <SettingField key={k} label={l} value={String(settings.data![k])} onSave={(v) => saveSetting(k, v)} />
          ))}
        </Card>
      </Section>
    </div>
  );
}

function SettingField({ label, value, onSave }: { label: string; value: string; onSave: (v: string) => void }) {
  const [v, setV] = useState(value);
  return <Field label={label}><div className="flex gap-2"><input className={inputCls} value={v} onChange={(e) => setV(e.target.value)} inputMode="decimal" /><Btn tone="soft" onClick={() => onSave(v)}>💾</Btn></div></Field>;
}
