"use client";
import { Card } from "@/components/ui";
import { PageHeader } from "@/components/Shell";
import { Loading, useAdminGet } from "@/components/admin/parts";
import { when } from "@/lib/format";

interface A { id: number; actor_id: number | null; action: string; entity: string | null; entity_id: string | null; before: unknown; after: unknown; source: string; at: string }

export default function Audit() {
  const list = useAdminGet<A[]>("/audit-logs?limit=100");
  if (!list.data) return <Loading />;
  return (
    <div className="space-y-4">
      <PageHeader title="Audit log" />
      {list.data.map((a) => (
        <Card key={a.id} className="space-y-1 text-sm" >
          <div className="flex justify-between"><b>{a.action}</b><span className="text-xs text-hint">{when(a.at)}</span></div>
          <div className="text-hint">admin {a.actor_id ?? "system"} · {a.entity} {a.entity_id} · {a.source}</div>
          {(a.before !== null || a.after !== null) && <div className="break-all font-mono text-xs">{JSON.stringify(a.before)} → {JSON.stringify(a.after)}</div>}
        </Card>
      ))}
    </div>
  );
}
