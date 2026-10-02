"use client";
import clsx from "clsx";
import { create } from "zustand";
import type { ButtonHTMLAttributes, ReactNode } from "react";
import { useEffect } from "react";
import { haptic } from "@/lib/tma";
import { useT } from "@/lib/i18n";
import type { OrderStatus } from "@/lib/api";

/* ---------- toasts ---------- */
interface ToastState { items: { id: number; text: string; tone: "ok" | "err" }[]; push: (text: string, tone?: "ok" | "err") => void }
export const useToast = create<ToastState>((set) => ({
  items: [],
  push: (text, tone = "ok") => {
    const id = Date.now() + Math.random();
    set((s) => ({ items: [...s.items, { id, text, tone }] }));
    haptic(tone === "ok" ? "success" : "error");
    setTimeout(() => set((s) => ({ items: s.items.filter((i) => i.id !== id) })), 3200);
  },
}));
export function Toaster() {
  const items = useToast((s) => s.items);
  return (
    <div className="pointer-events-none fixed inset-x-0 top-3 z-50 flex flex-col items-center gap-2 px-4" aria-live="polite">
      {items.map((i) => (
        <div key={i.id} className={clsx("pop pointer-events-auto max-w-sm rounded-2xl px-4 py-2.5 text-sm font-medium text-white shadow-lg", i.tone === "ok" ? "bg-success" : "bg-danger")}>
          {i.text}
        </div>
      ))}
    </div>
  );
}

/* ---------- primitives ---------- */
export function Card({ children, className, onClick }: { children: ReactNode; className?: string; onClick?: () => void }) {
  return (
    <div onClick={onClick} className={clsx("rounded-2xl bg-surface p-4 shadow-[0_1px_2px_rgba(0,0,0,.06)]", onClick && "cursor-pointer active:opacity-80", className)}>
      {children}
    </div>
  );
}

type Tone = "primary" | "success" | "danger" | "ghost" | "premium" | "stars" | "soft";
export function Btn({ tone = "primary", full, className, children, loading, ...rest }: ButtonHTMLAttributes<HTMLButtonElement> & { tone?: Tone; full?: boolean; loading?: boolean }) {
  const tones: Record<Tone, string> = {
    primary: "bg-accent text-white",
    success: "bg-success text-white",
    danger: "border border-danger text-danger bg-transparent",
    ghost: "bg-transparent text-accent",
    soft: "border border-line bg-surface text-ink",
    premium: "text-white [background:var(--premium-gradient)]",
    stars: "text-black [background:var(--stars-gradient)]",
  };
  return (
    <button
      {...rest}
      disabled={rest.disabled || loading}
      onClick={(e) => { haptic("tap"); rest.onClick?.(e); }}
      className={clsx("inline-flex h-11 items-center justify-center gap-2 rounded-xl px-4 font-semibold transition active:scale-[.98] disabled:opacity-50", tones[tone], full && "w-full", className)}
    >
      {loading && <Spinner />}
      {children}
    </button>
  );
}

export function Spinner({ className }: { className?: string }) {
  return <span className={clsx("inline-block h-4 w-4 animate-spin rounded-full border-2 border-current border-t-transparent", className)} />;
}

export function Skeleton({ className }: { className?: string }) {
  return <div className={clsx("skeleton h-5", className)} />;
}

export function Badge({ children, tone = "soft" }: { children: ReactNode; tone?: "ok" | "warn" | "err" | "soft" | "info" }) {
  const t = { ok: "bg-success/15 text-success", warn: "bg-warning/20 text-warning", err: "bg-danger/15 text-danger", soft: "bg-bg2 text-hint", info: "bg-accent/15 text-accent" }[tone];
  return <span className={clsx("inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold", t)}>{children}</span>;
}

export function StatusBadge({ status }: { status: OrderStatus }) {
  const { t } = useT();
  const tone = ({ completed: "ok", paid: "info", processing: "info", awaiting_payment: "warn", needs_review: "warn", failed: "err", refunded: "soft", expired: "soft", cancelled: "soft" } as const)[status];
  return <Badge tone={tone}>{t(`st_${status}`)}</Badge>;
}

export function Segmented<T extends string>({ value, options, onChange }: { value: T; options: { value: T; label: ReactNode }[]; onChange: (v: T) => void }) {
  return (
    <div className="flex rounded-xl bg-bg2 p-1">
      {options.map((o) => (
        <button key={o.value} onClick={() => { haptic("select"); onChange(o.value); }}
          className={clsx("flex-1 rounded-lg px-3 py-2 text-sm font-semibold transition", value === o.value ? "bg-surface text-ink shadow-sm" : "text-hint")}>
          {o.label}
        </button>
      ))}
    </div>
  );
}

export function Chips<T extends string>({ value, options, onChange }: { value: T; options: { value: T; label: string }[]; onChange: (v: T) => void }) {
  return (
    <div className="no-scrollbar -mx-4 flex gap-2 overflow-x-auto px-4">
      {options.map((o) => (
        <button key={o.value} onClick={() => onChange(o.value)} className={clsx("shrink-0 rounded-full px-3.5 py-1.5 text-sm font-medium", value === o.value ? "bg-accent text-white" : "bg-surface text-ink")}>
          {o.label}
        </button>
      ))}
    </div>
  );
}

export function Field({ label, children, hint }: { label?: string; children: ReactNode; hint?: ReactNode }) {
  return (
    <label className="block">
      {label && <div className="mb-1 text-sm font-medium text-hint">{label}</div>}
      {children}
      {hint && <div className="mt-1 text-xs text-hint">{hint}</div>}
    </label>
  );
}
export const inputCls = "h-11 w-full rounded-xl border border-line bg-surface px-3 text-ink outline-none focus:border-accent";

export function Section({ title, action, children }: { title?: string; action?: ReactNode; children: ReactNode }) {
  return (
    <section className="space-y-2">
      {(title || action) && (
        <div className="flex items-center justify-between px-1">
          <h2 className="text-[17px] font-semibold">{title}</h2>
          {action}
        </div>
      )}
      {children}
    </section>
  );
}

export function Empty({ icon = "📭", text }: { icon?: string; text: string }) {
  return (
    <div className="flex flex-col items-center gap-2 py-12 text-center text-hint">
      <div className="text-4xl">{icon}</div>
      <div>{text}</div>
    </div>
  );
}

export function ErrorBox({ error, onRetry }: { error: unknown; onRetry?: () => void }) {
  const { t } = useT();
  const code = (error as { code?: string })?.code;
  return (
    <Card className="space-y-3 text-center">
      <div className="text-3xl">⚠️</div>
      <div className="font-medium">{(code && t(`err_${code}`) !== `err_${code}` ? t(`err_${code}`) : (error as Error)?.message) || t("error_generic")}</div>
      {onRetry && <Btn tone="soft" onClick={onRetry}>{t("retry")}</Btn>}
    </Card>
  );
}

export function Modal({ open, onClose, title, children }: { open: boolean; onClose: () => void; title: string; children: ReactNode }) {
  useEffect(() => {
    if (!open) return;
    const h = (e: KeyboardEvent) => e.key === "Escape" && onClose();
    window.addEventListener("keydown", h);
    return () => window.removeEventListener("keydown", h);
  }, [open, onClose]);
  if (!open) return null;
  return (
    <div className="fixed inset-0 z-40 flex items-end justify-center bg-black/50 sm:items-center" onClick={onClose}>
      <div className="safe-bottom w-full max-w-md space-y-3 rounded-t-3xl bg-surface p-5 sm:rounded-3xl" onClick={(e) => e.stopPropagation()}>
        <div className="text-lg font-semibold">{title}</div>
        {children}
      </div>
    </div>
  );
}

export function ConfirmDialog({ open, title, text, danger, onConfirm, onClose, confirmLabel = "OK" }: { open: boolean; title: string; text?: string; danger?: boolean; onConfirm: () => void; onClose: () => void; confirmLabel?: string }) {
  return (
    <Modal open={open} onClose={onClose} title={title}>
      {text && <p className="text-hint">{text}</p>}
      <div className="flex gap-2">
        <Btn tone="soft" full onClick={onClose}>✕</Btn>
        <Btn tone={danger ? "danger" : "success"} full onClick={() => { onClose(); onConfirm(); }}>{confirmLabel}</Btn>
      </div>
    </Modal>
  );
}

export function Price({ usd, sub, big }: { usd: string; sub?: string; big?: boolean }) {
  return (
    <div className="text-right">
      <div className={clsx("num font-bold", big ? "text-[28px] leading-8" : "text-base")}>{usd}</div>
      {sub && <div className="num text-xs text-hint">{sub}</div>}
    </div>
  );
}
