"use client";
import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { useState } from "react";
import { Card, Chips, Empty, inputCls } from "@/components/ui";
import { PageHeader } from "@/components/Shell";
import { Loading } from "@/components/admin/parts";
import { api } from "@/lib/api";
import { usd } from "@/lib/format";

interface U { id: number; username: string | null; name: string | null; balance_usd: string; total_spent_usd: string; orders_count: number; is_banned: boolean; language: string }

export default function AdminUsers() {
  const [q, setQ] = useState("");
  const [sort, setSort] = useState("new");
  const data = useQuery({ queryKey: ["admin", "users", q, sort], queryFn: () => api.get<{ items: U[] }>(`/admin/users?limit=50&sort=${sort}${q ? `&q=${encodeURIComponent(q)}` : ""}`) });
  return (
    <div className="space-y-4">
      <PageHeader title="Foydalanuvchilar" />
      <input className={inputCls} placeholder="🔍 ID, @username yoki ism" value={q} onChange={(e) => setQ(e.target.value)} data-testid="user-search" />
      <Chips value={sort} onChange={setSort} options={[{ value: "new", label: "🆕 Yangilar" }, { value: "spent", label: "💰 Ko'p xarid" }, { value: "balance", label: "💼 Balans" }]} />
      {data.isLoading && <Loading />}
      {data.data?.items.length === 0 && <Empty text="Topilmadi" />}
      {data.data?.items.map((u) => (
        <Link key={u.id} href={`/admin/users/${u.id}`} data-testid="admin-user-row">
          <Card className="mb-2 flex items-center justify-between">
            <div><div className="font-semibold">{u.name} {u.is_banned && "⛔️"}</div><div className="text-xs text-hint">@{u.username ?? "-"} · {u.id} · {u.language}</div></div>
            <div className="text-right text-sm"><div className="num font-semibold">{usd(u.total_spent_usd)}</div><div className="num text-xs text-hint">balans {usd(u.balance_usd)} · {u.orders_count} ta</div></div>
          </Card>
        </Link>
      ))}
    </div>
  );
}
