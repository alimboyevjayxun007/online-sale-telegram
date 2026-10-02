"use client";
import { useState } from "react";
import { Btn, Card, Section } from "@/components/ui";
import { PageHeader } from "@/components/Shell";
import { Kpi, Loading, MethodsDonut, MoneyChart, Panel, PeriodSwitcher, ProductsChart, UsersChart, useAdminGet } from "@/components/admin/parts";
import { initDataRaw } from "@/lib/tma";
import { usd } from "@/lib/format";

interface Dash { current: Record<string, number | string | Record<string, string>>; previous: Record<string, number | string | Record<string, string>>; change_pct: Record<string, number | null>; derived: Record<string, number | string | null> }

export default function StatsPage() {
  const [period, setPeriod] = useState("month");
  const d = useAdminGet<Dash>(`/dashboard?period=${period}`);
  const s = useAdminGet<Record<string, string>[]>(`/stats/timeseries?period=${period}&metrics=revenue_usd,cost_usd,gross_profit_usd,premium_3m,premium_6m,premium_12m,stars_orders,new_users,active_users`);
  const prod = useAdminGet<{ key: string; orders: number; revenue_usd: string }[]>(`/stats/breakdown?by=product&period=${period}`);
  const lang = useAdminGet<{ key: string; orders: number; revenue_usd: string }[]>(`/stats/breakdown?by=language&period=${period}`);
  const src = useAdminGet<{ key: string; orders: number; revenue_usd: string }[]>(`/stats/breakdown?by=source&period=${period}`);
  const top = useAdminGet<{ id: number; name: string | null; username: string | null; orders: number; spent_usd: string }[]>(`/stats/top-buyers?period=${period}&limit=10`);
  const download = async () => {
    const r = await fetch(`/api/v1/admin/stats/export.xlsx?period=${period}`, { headers: { Authorization: `tma ${initDataRaw()}` } });
    const url = URL.createObjectURL(await r.blob());
    const a = Object.assign(document.createElement("a"), { href: url, download: `stats_${period}.xlsx` });
    a.click();
    URL.revokeObjectURL(url);
  };
  if (!d.data) return <Loading />;
  const c = d.data.current as Record<string, string | number>;
  const p = d.data.previous as Record<string, string | number>;
  const table = (rows?: { key: string; orders: number; revenue_usd: string }[]) => (
    <Card className="divide-y divide-line !p-0">
      {rows?.length ? rows.map((r) => <div key={r.key} className="flex justify-between px-4 py-2.5 text-sm"><span>{r.key}</span><span className="num">{r.orders} ta · {usd(r.revenue_usd)}</span></div>) : <div className="p-4 text-center text-hint">Ma&apos;lumot yo&apos;q</div>}
    </Card>
  );
  return (
    <div className="space-y-4">
      <PageHeader title="Statistika" right={<Btn tone="soft" onClick={download}>📥 Excel</Btn>} />
      <PeriodSwitcher value={period} onChange={setPeriod} />
      <Card className="space-y-1 text-sm">
        {[["Sotuv", "revenue_usd"], ["Tannarx", "cost_usd"], ["Yalpi foyda", "gross_profit_usd"], ["Xarajatlar", "expenses_usd"], ["Referal bonus", "referral_usd"], ["Sof foyda", "net_profit_usd"]].map(([label, key]) => (
          <div key={key} className="flex justify-between"><span className="text-hint">{label}</span><span className="num"><b>{usd(c[key])}</b> <span className="text-xs text-hint">oldingi: {usd(p[key])}</span></span></div>
        ))}
      </Card>
      <div className="grid grid-cols-2 gap-3">
        <Kpi label="Buyurtmalar" value={`${c.orders_completed}`} change={d.data.change_pct.orders_completed} />
        <Kpi label="Xaridorlar" value={`${c.paying_users}`} change={d.data.change_pct.paying_users} />
        <Kpi label="Yangi userlar" value={`${c.new_users}`} change={d.data.change_pct.new_users} />
        <Kpi label="Konversiya" value={`${d.data.derived.conversion_pct ?? "—"}%`} sub={`muvaffaqiyat ${d.data.derived.success_rate_pct ?? "—"}%`} />
      </div>
      <Panel title="Sotuv / Tannarx / Foyda"><MoneyChart rows={s.data ?? []} /></Panel>
      <Panel title="Mahsulotlar"><ProductsChart rows={s.data ?? []} /></Panel>
      <Panel title="Foydalanuvchilar"><UsersChart rows={s.data ?? []} /></Panel>
      <Panel title="To'lov usullari"><MethodsDonut data={(c.revenue_by_method as unknown as Record<string, string>) ?? {}} /></Panel>
      <Section title="Mahsulot bo'yicha">{table(prod.data)}</Section>
      <Section title="Til bo'yicha">{table(lang.data)}</Section>
      <Section title="Manba bo'yicha (src_*)">{table(src.data)}</Section>
      <Section title="🏆 Top xaridorlar">
        <Card className="divide-y divide-line !p-0">
          {top.data?.length ? top.data.map((t, i) => <div key={t.id} className="flex justify-between px-4 py-2.5 text-sm"><span>{i + 1}. {t.name ?? t.username ?? t.id}</span><span className="num">{usd(t.spent_usd)} · {t.orders}</span></div>) : <div className="p-4 text-center text-hint">Ma&apos;lumot yo&apos;q</div>}
        </Card>
      </Section>
    </div>
  );
}
