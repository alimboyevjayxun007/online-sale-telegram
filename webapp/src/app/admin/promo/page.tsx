"use client";
import { useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { Badge, Btn, Card, Field, Section, Segmented, inputCls, useToast } from "@/components/ui";
import { PageHeader } from "@/components/Shell";
import { Loading, useAdminGet } from "@/components/admin/parts";
import { api, ApiError } from "@/lib/api";

interface P { id: number; code: string; type: string; value: string; applies_to: string; max_uses: number | null; used_count: number; is_active: boolean }

export default function Promo() {
  const qc = useQueryClient();
  const push = useToast((s) => s.push);
  const list = useAdminGet<P[]>("/promo-codes");
  const [f, setF] = useState({ code: "", type: "percent", value: "", max: "" });
  const reload = () => qc.invalidateQueries({ queryKey: ["admin", "/promo-codes"] });
  const create = async () => {
    try { await api.post("/admin/promo-codes", { code: f.code, type: f.type, value: f.value, max_uses: f.max ? Number(f.max) : null }); push("✅ Yaratildi"); setF({ code: "", type: "percent", value: "", max: "" }); reload(); }
    catch (e) { push(e instanceof ApiError ? e.message : "Xato", "err"); }
  };
  if (!list.data) return <Loading />;
  return (
    <div className="space-y-4">
      <PageHeader title="Promokodlar" />
      <Card className="space-y-3">
        <Segmented value={f.type} onChange={(type) => setF({ ...f, type })} options={[{ value: "percent", label: "% foiz" }, { value: "fixed_usd", label: "$ qat'iy" }]} />
        <div className="grid grid-cols-3 gap-2">
          <Field label="Kod"><input className={inputCls} value={f.code} onChange={(e) => setF({ ...f, code: e.target.value })} data-testid="promo-code" /></Field>
          <Field label="Qiymat"><input className={inputCls} inputMode="decimal" value={f.value} onChange={(e) => setF({ ...f, value: e.target.value })} data-testid="promo-value" /></Field>
          <Field label="Limit"><input className={inputCls} inputMode="numeric" value={f.max} onChange={(e) => setF({ ...f, max: e.target.value })} placeholder="∞" /></Field>
        </div>
        <Btn tone="success" full disabled={!f.code || !f.value} onClick={create} data-testid="promo-create">➕ Yaratish</Btn>
      </Card>
      <Section title="Ro'yxat">
        <Card className="divide-y divide-line !p-0">
          {list.data.map((p) => (
            <div key={p.id} className="flex items-center justify-between px-4 py-3">
              <div><b>{p.code}</b> <span className="text-sm text-hint">{p.value}{p.type === "percent" ? "%" : "$"} · {p.used_count}/{p.max_uses ?? "∞"}</span></div>
              {p.is_active ? <Btn tone="danger" className="!h-8 !px-3 text-sm" onClick={async () => { await api.del(`/admin/promo-codes/${p.id}`); reload(); }}>O&apos;chirish</Btn> : <Badge>o&apos;chirilgan</Badge>}
            </div>
          ))}
        </Card>
      </Section>
    </div>
  );
}
