"use client";
import { useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { Btn, Card, Field, Section, Segmented, inputCls, useToast } from "@/components/ui";
import { PageHeader } from "@/components/Shell";
import { Loading, useAdminGet } from "@/components/admin/parts";
import { api, ApiError } from "@/lib/api";

export default function Admins() {
  const qc = useQueryClient();
  const push = useToast((s) => s.push);
  const list = useAdminGet<{ user_id: number; role: string }[]>("/admins");
  const [uid, setUid] = useState("");
  const [role, setRole] = useState<"admin" | "support">("support");
  const reload = () => qc.invalidateQueries({ queryKey: ["admin", "/admins"] });
  if (!list.data) return <Loading />;
  return (
    <div className="space-y-4">
      <PageHeader title="Adminlar" />
      <Card className="divide-y divide-line !p-0">
        {list.data.map((a) => (
          <div key={a.user_id} className="flex items-center justify-between px-4 py-3"><span><b>{a.user_id}</b> <span className="text-sm text-hint">{a.role}</span></span>{a.role !== "owner" && <Btn tone="danger" className="!h-8 !px-3" onClick={async () => { await api.del(`/admin/admins/${a.user_id}`); reload(); }}>🗑</Btn>}</div>
        ))}
      </Card>
      <Section title="Admin qo'shish">
        <Card className="space-y-3">
          <Field label="Telegram ID (foydalanuvchi botni ishga tushirgan bo'lishi kerak)"><input className={inputCls} inputMode="numeric" value={uid} onChange={(e) => setUid(e.target.value)} data-testid="admin-uid" /></Field>
          <Segmented value={role} onChange={setRole} options={[{ value: "support", label: "support" }, { value: "admin", label: "admin" }]} />
          <Btn tone="success" full disabled={!uid} data-testid="admin-add" onClick={async () => { try { await api.post("/admin/admins", { user_id: Number(uid), role }); push("✅ OK"); setUid(""); reload(); } catch (e) { push(e instanceof ApiError ? e.message : "Xato", "err"); } }}>➕ Qo&apos;shish</Btn>
        </Card>
      </Section>
    </div>
  );
}
