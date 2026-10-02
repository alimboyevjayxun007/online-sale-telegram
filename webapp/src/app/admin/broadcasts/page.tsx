"use client";
import { useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { Badge, Btn, Card, ConfirmDialog, Field, Section, inputCls, useToast } from "@/components/ui";
import { PageHeader } from "@/components/Shell";
import { Loading, useAdminGet } from "@/components/admin/parts";
import { api, ApiError } from "@/lib/api";

interface B { id: number; status: string; total: number; sent: number; failed: number; percent: number }
const SEGMENTS: Record<string, { label: string; segment: Record<string, unknown> }> = {
  all: { label: "👥 Hammaga", segment: {} },
  uz: { label: "🇺🇿 uz", segment: { language: ["uz"] } },
  ru: { label: "🇷🇺 ru", segment: { language: ["ru"] } },
  en: { label: "🇬🇧 en", segment: { language: ["en"] } },
  buyers: { label: "💰 Xaridorlar", segment: { has_orders: true } },
  inactive: { label: "😴 30 kun nofaol", segment: { inactive_days: 30 } },
};

export default function Broadcasts() {
  const qc = useQueryClient();
  const push = useToast((s) => s.push);
  const list = useAdminGet<B[]>("/broadcasts", true, 5000);
  const [text, setText] = useState("");
  const [btnText, setBtnText] = useState("");
  const [btnUrl, setBtnUrl] = useState("");
  const [seg, setSeg] = useState("all");
  const [draft, setDraft] = useState<B | null>(null);
  const [go, setGo] = useState(false);
  const reload = () => qc.invalidateQueries({ queryKey: ["admin", "/broadcasts"] });
  const content = () => ({ type: "text", text, ...(btnText && btnUrl ? { buttons: [[{ text: btnText, url: btnUrl }]] } : {}) });
  const create = async () => {
    try { const b = await api.post<B>("/admin/broadcasts", { content: content(), segment: SEGMENTS[seg].segment }); setDraft(b); reload(); }
    catch (e) { push(e instanceof ApiError ? e.message : "Xato", "err"); }
  };
  const action = async (id: number, a: string) => { try { await api.post(`/admin/broadcasts/${id}/${a}`, {}); push("✅ OK"); reload(); if (draft?.id === id && a !== "preview") setDraft(null); } catch (e) { push(e instanceof ApiError ? e.message : "Xato", "err"); } };
  if (!list.data) return <Loading />;
  return (
    <div className="space-y-4">
      <PageHeader title="Xabar yuborish" />
      <Card className="space-y-3">
        <Field label="Matn (HTML: <b>, <i>, <a>)"><textarea className={`${inputCls} h-28 py-2`} value={text} onChange={(e) => setText(e.target.value)} data-testid="bc-text" /></Field>
        <div className="grid grid-cols-2 gap-2"><input className={inputCls} placeholder="Tugma matni" value={btnText} onChange={(e) => setBtnText(e.target.value)} /><input className={inputCls} placeholder="https://..." value={btnUrl} onChange={(e) => setBtnUrl(e.target.value)} /></div>
        <Field label="Kimga?">
          <div className="flex flex-wrap gap-2">{Object.entries(SEGMENTS).map(([k, s]) => <button key={k} onClick={() => setSeg(k)} className={`rounded-full px-3 py-1.5 text-sm ${seg === k ? "bg-accent text-white" : "bg-bg2"}`}>{s.label}</button>)}</div>
        </Field>
        {/* live preview, shaped like a Telegram message */}
        {text && <div className="rounded-2xl rounded-bl-sm bg-bg2 p-3 text-sm"><div className="whitespace-pre-wrap" dangerouslySetInnerHTML={{ __html: text.replace(/<(?!\/?(b|i|u|s|code)\b)[^>]*>/g, "").replace(/<(b|i|u|s|code)\b[^>]*>/g, "<$1>") }} />{btnText && <div className="mt-2 rounded-lg bg-accent/20 py-1.5 text-center text-accent">{btnText}</div>}</div>}
        {!draft ? <Btn tone="primary" full disabled={!text} onClick={create} data-testid="bc-create">Oldindan ko&apos;rish va qabul qiluvchilar soni</Btn> : (
          <div className="space-y-2">
            <div className="text-center">Qabul qiluvchilar: <b className="num">~{draft.total}</b></div>
            <div className="grid grid-cols-2 gap-2"><Btn tone="soft" onClick={() => action(draft.id, "preview")}>🧪 O&apos;zimga test</Btn><Btn tone="success" onClick={() => setGo(true)}>🚀 Yuborish</Btn></div>
          </div>
        )}
      </Card>
      <Section title="So'nggi xabarlar">
        {list.data.map((b) => (
          <Card key={b.id} className="mb-2 space-y-2">
            <div className="flex items-center justify-between"><b>#{b.id}</b><Badge tone={b.status === "completed" ? "ok" : b.status === "running" ? "info" : "soft"}>{b.status}</Badge></div>
            <div className="h-2 overflow-hidden rounded-full bg-bg2"><div className="h-full bg-success" style={{ width: `${b.percent}%` }} /></div>
            <div className="num text-xs text-hint">{b.sent + b.failed} / {b.total} · ❌ {b.failed}</div>
            {b.status === "running" && <div className="flex gap-2"><Btn tone="soft" onClick={() => action(b.id, "pause")}>⏸</Btn><Btn tone="danger" onClick={() => action(b.id, "cancel")}>⏹</Btn></div>}
            {b.status === "paused" && <div className="flex gap-2"><Btn tone="success" onClick={() => action(b.id, "start")}>▶️</Btn><Btn tone="danger" onClick={() => action(b.id, "cancel")}>⏹</Btn></div>}
          </Card>
        ))}
      </Section>
      <ConfirmDialog open={go} onClose={() => setGo(false)} title={`${draft?.total ?? 0} kishiga yuborilsinmi?`} confirmLabel="Yuborish" onConfirm={() => draft && action(draft.id, "start")} />
    </div>
  );
}
