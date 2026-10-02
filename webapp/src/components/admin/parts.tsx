"use client";
import { useQuery } from "@tanstack/react-query";
import clsx from "clsx";
import type { ReactNode } from "react";
import { Area, AreaChart, Bar, BarChart, CartesianGrid, Cell, Legend, Line, LineChart, Pie, PieChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { api } from "@/lib/api";
import { pct } from "@/lib/format";
import { Card, Chips, Skeleton } from "../ui";

export const PERIODS = [
  { value: "today", label: "Bugun" },
  { value: "week", label: "Hafta" },
  { value: "month", label: "Oy" },
  { value: "year", label: "Yil" },
];

export function useAdminGet<T>(path: string, enabled = true, refetchMs?: number) {
  return useQuery({ queryKey: ["admin", path], queryFn: () => api.get<T>(`/admin${path}`), enabled, refetchInterval: refetchMs });
}

export function PeriodSwitcher({ value, onChange }: { value: string; onChange: (v: string) => void }) {
  return <Chips value={value} onChange={onChange} options={PERIODS} />;
}

export function Kpi({ label, value, change, tone, sub, testid }: { label: string; value: string; change?: number | null; tone?: "good" | "bad"; sub?: string; testid?: string }) {
  const up = (change ?? 0) >= 0;
  return (
    <Card className="space-y-1 !p-3.5" >
      <div className="text-xs font-medium text-hint">{label}</div>
      <div className={clsx("num text-xl font-bold", tone === "bad" && "text-danger")} data-testid={testid}>{value}</div>
      {change !== undefined && change !== null ? <div className={clsx("num text-xs font-semibold", up ? "text-success" : "text-danger")}>{pct(change)}</div> : sub ? <div className="text-xs text-hint">{sub}</div> : <div className="h-4" />}
    </Card>
  );
}

export const COLORS = { revenue: "var(--success)", cost: "var(--danger)", profit: "var(--profit)", accent: "var(--accent)", premium3: "#6B93FF", premium6: "#976FFF", premium12: "#E46ACE", stars: "#FFB300", ton: "var(--ton)", balance: "#8E8E93" };

const axis = { stroke: "var(--hint)", fontSize: 11, tickLine: false, axisLine: false } as const;
const tip = { contentStyle: { background: "var(--surface)", border: "1px solid var(--border)", borderRadius: 12, color: "var(--text)" } } as const;
const short = (t: string) => (t.length > 10 ? t.slice(11, 16) : t.slice(5));

export function Panel({ title, children, h = 200 }: { title: string; children: ReactNode; h?: number }) {
  return (
    <Card className="space-y-2 !p-3.5">
      <div className="text-sm font-semibold">{title}</div>
      <div style={{ height: h }}>{children}</div>
    </Card>
  );
}

type Row = Record<string, string | number>;
const num = (rows: Row[]) => rows.map((r) => Object.fromEntries(Object.entries(r).map(([k, v]) => [k, k === "t" ? v : Number(v)])));

export function MoneyChart({ rows }: { rows: Row[] }) {
  if (!rows.length) return <NoData />;
  return (
    <ResponsiveContainer width="100%" height="100%">
      <AreaChart data={num(rows)} margin={{ left: -18, right: 4, top: 4 }}>
        <CartesianGrid stroke="var(--border)" vertical={false} />
        <XAxis dataKey="t" tickFormatter={short} {...axis} />
        <YAxis {...axis} />
        <Tooltip {...tip} />
        <Area type="monotone" dataKey="revenue_usd" name="Sotuv" stroke={COLORS.revenue} fill={COLORS.revenue} fillOpacity={0.18} />
        <Area type="monotone" dataKey="cost_usd" name="Tannarx" stroke={COLORS.cost} fill={COLORS.cost} fillOpacity={0.12} />
        <Line type="monotone" dataKey="gross_profit_usd" name="Foyda" stroke={COLORS.profit} strokeWidth={2} dot={false} />
      </AreaChart>
    </ResponsiveContainer>
  );
}

export function ProductsChart({ rows }: { rows: Row[] }) {
  if (!rows.length) return <NoData />;
  return (
    <ResponsiveContainer width="100%" height="100%">
      <BarChart data={num(rows)} margin={{ left: -18, right: 4, top: 4 }}>
        <CartesianGrid stroke="var(--border)" vertical={false} />
        <XAxis dataKey="t" tickFormatter={short} {...axis} />
        <YAxis allowDecimals={false} {...axis} />
        <Tooltip {...tip} />
        <Legend wrapperStyle={{ fontSize: 11 }} />
        <Bar dataKey="premium_3m" name="3 oy" stackId="a" fill={COLORS.premium3} />
        <Bar dataKey="premium_6m" name="6 oy" stackId="a" fill={COLORS.premium6} />
        <Bar dataKey="premium_12m" name="12 oy" stackId="a" fill={COLORS.premium12} />
        <Bar dataKey="stars_orders" name="Stars" stackId="a" fill={COLORS.stars} radius={[4, 4, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
}

export function UsersChart({ rows }: { rows: Row[] }) {
  if (!rows.length) return <NoData />;
  return (
    <ResponsiveContainer width="100%" height="100%">
      <LineChart data={num(rows)} margin={{ left: -18, right: 4, top: 4 }}>
        <CartesianGrid stroke="var(--border)" vertical={false} />
        <XAxis dataKey="t" tickFormatter={short} {...axis} />
        <YAxis allowDecimals={false} {...axis} />
        <Tooltip {...tip} />
        <Line type="monotone" dataKey="new_users" name="Yangi" stroke={COLORS.accent} strokeWidth={2} dot={false} />
        <Line type="monotone" dataKey="active_users" name="Faol" stroke={COLORS.stars} strokeWidth={2} dot={false} />
      </LineChart>
    </ResponsiveContainer>
  );
}

export function MethodsDonut({ data }: { data: Record<string, string> }) {
  const rows = Object.entries(data).map(([k, v]) => ({ name: k, value: Number(v) })).filter((r) => r.value > 0);
  if (!rows.length) return <NoData />;
  const color = (n: string) => (n === "ton" ? COLORS.ton : n === "stars" ? COLORS.stars : COLORS.balance);
  return (
    <ResponsiveContainer width="100%" height="100%">
      <PieChart>
        <Pie data={rows} dataKey="value" nameKey="name" innerRadius={45} outerRadius={75} paddingAngle={2}>
          {rows.map((r) => <Cell key={r.name} fill={color(r.name)} />)}
        </Pie>
        <Tooltip {...tip} />
        <Legend wrapperStyle={{ fontSize: 11 }} />
      </PieChart>
    </ResponsiveContainer>
  );
}

export function NoData() {
  return <div className="flex h-full items-center justify-center text-sm text-hint">Ma&apos;lumot yo&apos;q</div>;
}

export function Loading() {
  return <div className="space-y-3"><Skeleton className="h-24" /><Skeleton className="h-24" /><Skeleton className="h-40" /></div>;
}

export function KV({ k, v }: { k: string; v: ReactNode }) {
  return <div className="flex items-start justify-between gap-3 py-1.5 text-sm"><span className="text-hint">{k}</span><span className="num text-right font-medium">{v}</span></div>;
}
