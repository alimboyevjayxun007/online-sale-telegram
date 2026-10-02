"use client";
import Link from "next/link";
import { useState } from "react";
import { Card, ErrorBox } from "@/components/ui";
import { PageHeader } from "@/components/Shell";
import { Kpi, Loading, MethodsDonut, MoneyChart, Panel, PeriodSwitcher, ProductsChart, UsersChart, useAdminGet } from "@/components/admin/parts";
import { ton, usd } from "@/lib/format";

interface Dash {
  period: { granularity: string };
  current: Record<string, number | string | Record<string, string>>;
  change_pct: Record<string, number | null>;
  derived: { margin_pct: number; avg_order_usd: string; success_rate_pct: number | null; conversion_pct: number | null };
  totals: { users: number; blocked_users: number; needs_review: number; user_balances_usd: string };
  activity: { dau: number; wau: number; mau: number };
  wallets: { hot_wallet: { balance_ton: string | null; address: string }; stars_ledger: number; stars_balance?: number | null };
}

export default function AdminDashboard() {
  const [period, setPeriod] = useState("today");
  const d = useAdminGet<Dash>(`/dashboard?period=${period}`, true, 30000);
  const series = useAdminGet<Record<string, string>[]>(`/stats/timeseries?period=${period}&metrics=revenue_usd,cost_usd,gross_profit_usd,orders_completed,premium_3m,premium_6m,premium_12m,stars_orders,new_users,active_users`);
  if (d.error) return <ErrorBox error={d.error} onRetry={() => d.refetch()} />;
  if (!d.data) return <Loading />;
  const c = d.data.current as Record<string, string | number>;
  const ch = d.data.change_pct;
  const methods = d.data.current.revenue_by_method as Record<string, string>;
  return (
    <div className="space-y-4">
      <PageHeader title="Dashboard" />
      <PeriodSwitcher value={period} onChange={setPeriod} />
      {d.data.totals.needs_review > 0 && (
        <Link href="/admin/orders?status=needs_review"><Card className="!bg-warning/15 text-sm font-semibold text-warning" data-testid="review-alert">⚠️ {d.data.totals.needs_review} ta buyurtma tekshirish kutmoqda ›</Card></Link>
      )}
      <div className="grid grid-cols-2 gap-3">
        <Kpi label="Kirim (cash-in)" value={usd(c.cash_in_usd)} change={ch.cash_in_usd} testid="kpi-cashin" />
        <Kpi label="Sotuv" value={usd(c.revenue_usd)} change={ch.revenue_usd} testid="kpi-revenue" />
        <Kpi label="Tannarx (chiqim)" value={usd(c.cost_usd)} change={ch.cost_usd} />
        <Kpi label="Sof foyda" value={usd(c.net_profit_usd)} change={ch.net_profit_usd} testid="kpi-profit" />
        <Kpi label="Buyurtmalar" value={`${c.orders_completed}`} change={ch.orders_completed} sub={`❌ ${c.orders_failed} · ↩️ ${c.orders_refunded}`} />
        <Kpi label="Yangi foydalanuvchilar" value={`+${c.new_users}`} change={ch.new_users} />
        <Kpi label="Faol" value={`${c.active_users}`} sub={`DAU ${d.data.activity.dau} · MAU ${d.data.activity.mau}`} />
        <Kpi label="O'rtacha chek" value={`${d.data.derived.avg_order_usd} $`} sub={`marja ${d.data.derived.margin_pct}%`} />
      </div>
      <Panel title="Sotuv / Tannarx / Foyda"><MoneyChart rows={series.data ?? []} /></Panel>
      <Panel title="Buyurtmalar (mahsulot bo'yicha)"><ProductsChart rows={series.data ?? []} /></Panel>
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
        <Panel title="To'lov usullari"><MethodsDonut data={methods ?? {}} /></Panel>
        <Panel title="Foydalanuvchilar"><UsersChart rows={series.data ?? []} /></Panel>
      </div>
      <Card className="space-y-2">
        <div className="flex justify-between"><span>💎 Hot wallet</span><b className="num">{d.data.wallets.hot_wallet.balance_ton ? `${ton(d.data.wallets.hot_wallet.balance_ton)} TON` : "—"}</b></div>
        <div className="flex justify-between"><span>⭐ Stars (ledger)</span><b className="num">{d.data.wallets.stars_ledger}</b></div>
        <div className="flex justify-between"><span>💼 Foydalanuvchi balanslari</span><b className="num">{usd(d.data.totals.user_balances_usd)}</b></div>
        <Link href="/admin/finance" className="block pt-1 text-sm text-accent">Moliya ›</Link>
      </Card>
    </div>
  );
}
