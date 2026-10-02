"use client";
import clsx from "clsx";
import { Check } from "lucide-react";
import { useEffect, useRef, useState, type ReactNode } from "react";
import { api, ApiError, type Me } from "@/lib/api";
import { useT } from "@/lib/i18n";
import { haptic } from "@/lib/tma";
import { Card, inputCls, Section, Segmented, Spinner } from "../ui";

export interface Recipient { type: "self" | "other"; username: string; ok: boolean; name?: string | null }

export function RecipientPicker({ me, product, months, value, onChange }: { me: Me; product: "premium" | "stars"; months?: number; value: Recipient; onChange: (r: Recipient) => void }) {
  const { t } = useT();
  const [state, setState] = useState<"idle" | "checking" | "ok" | "missing" | "cannot" | "unverified">("idle");
  const timer = useRef<ReturnType<typeof setTimeout>>(undefined);
  const noUsername = !me.username;

  useEffect(() => {
    if (value.type !== "other") return;
    clearTimeout(timer.current);
    const u = value.username.replace(/^@/, "").trim();
    if (!/^[A-Za-z][A-Za-z0-9_]{4,31}$/.test(u)) { setState("idle"); if (value.ok) onChange({ ...value, ok: false }); return; }
    setState("checking");
    timer.current = setTimeout(async () => {
      try {
        const r = await api.post<{ found: boolean; name: string | null; can_receive: boolean; verified?: boolean }>("/recipients/resolve", { username: u, product, months: months ?? 3 });
        if (!r.found) { setState("missing"); onChange({ ...value, ok: false }); }
        else if (!r.can_receive) { setState("cannot"); onChange({ ...value, ok: false }); }
        else { setState(r.verified === false ? "unverified" : "ok"); onChange({ ...value, username: u, ok: true, name: r.name }); }
      } catch { setState("idle"); }
    }, 500);
    return () => clearTimeout(timer.current);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [value.username, value.type, product, months]);

  return (
    <Section title={`1 · ${t("who")}`}>
      <Segmented
        value={value.type}
        options={[{ value: "self", label: `🙋 ${t("for_me")}` }, { value: "other", label: `🎁 ${t("for_friend")}` }]}
        onChange={(v) => onChange({ type: v, username: value.username, ok: v === "self" && (product === "premium" || !noUsername) })}
      />
      {value.type === "self" && product === "stars" && noUsername && <Card className="text-sm text-hint">ℹ️ Username → Telegram › Settings › Username</Card>}
      {value.type === "other" && (
        <div className="space-y-2">
          <input
            className={clsx(inputCls, (state === "missing" || state === "cannot") && "border-danger")}
            placeholder={t("username_ph")}
            value={value.username}
            autoCapitalize="none"
            autoCorrect="off"
            data-testid="username-input"
            onChange={(e) => onChange({ ...value, username: e.target.value, ok: false })}
          />
          <div className="min-h-5 px-1 text-sm">
            {state === "checking" && <span className="flex items-center gap-2 text-hint"><Spinner />{t("checking")}</span>}
            {state === "ok" && <span className="text-success">✅ {t("found", { name: value.name ?? value.username })}</span>}
            {state === "unverified" && <span className="text-warning">⚠️ {t("unverified")}</span>}
            {state === "missing" && <span className="text-danger">❌ {t("not_found")}</span>}
            {state === "cannot" && <span className="text-danger">❌ {t("cannot_receive")}</span>}
          </div>
        </div>
      )}
    </Section>
  );
}

export type Method = "ton" | "stars" | "balance";

export function MethodPicker({ value, onChange, options, step }: { value: Method; onChange: (m: Method) => void; options: { method: Method; label: string; sub: string; disabled?: boolean; note?: string }[]; step: number }) {
  const { t } = useT();
  return (
    <Section title={`${step} · ${t("pay_method")}`}>
      <Card className="divide-y divide-line !p-0">
        {options.map((o) => (
          <button key={o.method} disabled={o.disabled} onClick={() => { haptic("select"); onChange(o.method); }} className="flex w-full items-center gap-3 px-4 py-3 text-left disabled:opacity-50" data-testid={`method-${o.method}`}>
            <span className={clsx("flex h-5 w-5 items-center justify-center rounded-full border-2", value === o.method ? "border-accent bg-accent text-white" : "border-line")}>{value === o.method && <Check size={12} />}</span>
            <span className="flex-1">
              <span className="font-medium">{o.label}</span>
              {o.note && <span className="ml-2 text-xs text-warning">{o.note}</span>}
            </span>
            <span className="num text-sm text-hint">{o.sub}</span>
          </button>
        ))}
      </Card>
    </Section>
  );
}

export interface PromoState { code: string; discount: number; final: number }

export function PromoBox({ product, planId, stars, value, onChange }: { product: "premium" | "stars"; planId?: number; stars?: number; value: PromoState | null; onChange: (p: PromoState | null) => void }) {
  const { t } = useT();
  const [open, setOpen] = useState(false);
  const [code, setCode] = useState("");
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState(false);
  useEffect(() => { onChange(null); setErr(""); }, [planId, stars]);
  const apply = async () => {
    setBusy(true); setErr("");
    try {
      const r = await api.post<{ discount_usd: string; final_price_usd: string }>("/promo/validate", { code, product_type: product, plan_id: planId, stars_amount: stars });
      onChange({ code: code.trim(), discount: Number(r.discount_usd), final: Number(r.final_price_usd) });
      haptic("success");
    } catch (e) { setErr(e instanceof ApiError ? t("promo_bad") : t("error_generic")); haptic("error"); }
    finally { setBusy(false); }
  };
  if (value) return <Card className="flex items-center justify-between text-sm"><span>🎟 {value.code} · <span className="text-success">{t("promo_ok")}</span></span><button className="text-hint" onClick={() => onChange(null)}>✕</button></Card>;
  return (
    <div>
      <button className="px-1 text-sm font-medium text-accent" onClick={() => setOpen(!open)}>🎟 {t("promo")}</button>
      {open && (
        <div className="mt-2 flex gap-2">
          <input className={clsx(inputCls, err && "border-danger")} value={code} onChange={(e) => setCode(e.target.value)} placeholder="KOD" autoCapitalize="characters" data-testid="promo-input" />
          <button disabled={!code || busy} onClick={apply} className="h-11 shrink-0 rounded-xl bg-accent px-4 font-semibold text-white disabled:opacity-50" data-testid="promo-apply">{t("promo_apply")}</button>
        </div>
      )}
      {err && <div className="mt-1 px-1 text-sm text-danger">{err}</div>}
    </div>
  );
}

export function Hero({ kind, title, sub }: { kind: "premium" | "stars"; title: string; sub: string }) {
  return (
    <div className={clsx("relative overflow-hidden rounded-3xl p-5", kind === "premium" ? "text-white [background:var(--premium-gradient)]" : "text-black [background:var(--stars-gradient)]")}>
      <div className="float absolute -right-2 -top-2 text-7xl opacity-90">{kind === "premium" ? "💎" : "⭐"}</div>
      <div className="relative max-w-[70%]">
        <div className="text-[22px] font-bold leading-7">{title}</div>
        <div className="mt-1 text-sm opacity-90">{sub}</div>
      </div>
    </div>
  );
}

export function Row({ children, right }: { children: ReactNode; right?: ReactNode }) {
  return <div className="flex items-center justify-between gap-3">{children}{right}</div>;
}
