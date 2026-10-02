"use client";
import { beginCell } from "@ton/core";
import { useTonConnectUI, useTonWallet } from "@tonconnect/ui-react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import clsx from "clsx";
import { Check, ChevronDown, Copy } from "lucide-react";
import { useParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { MainAction } from "@/components/MainAction";
import { Btn, Card, ErrorBox, Skeleton, StatusBadge, useToast } from "@/components/ui";
import { PageHeader } from "@/components/Shell";
import { useBackButton } from "@/hooks/useBackButton";
import { api, ApiError, type OrderDetail, type OrderStatus, type PaymentInfo } from "@/lib/api";
import { num, ton as fmtTon, usd } from "@/lib/format";
import { useT } from "@/lib/i18n";
import { haptic, tg } from "@/lib/tma";

const TERMINAL: OrderStatus[] = ["completed", "failed", "refunded", "expired", "cancelled"];
const STEPS: OrderStatus[] = ["awaiting_payment", "paid", "processing", "completed"];

function useCountdown(iso?: string | null) {
  const [left, setLeft] = useState<number | null>(null);
  useEffect(() => {
    if (!iso) return setLeft(null);
    const tick = () => setLeft(Math.max(0, Math.floor((new Date(iso).getTime() - Date.now()) / 1000)));
    tick();
    const id = setInterval(tick, 1000);
    return () => clearInterval(id);
  }, [iso]);
  return left;
}
const mmss = (s: number) => `${Math.floor(s / 60).toString().padStart(2, "0")}:${(s % 60).toString().padStart(2, "0")}`;

export function tonPayload(comment: string): string {
  return beginCell().storeUint(0, 32).storeStringTail(comment).endCell().toBoc().toString("base64");
}

function Confetti() {
  const colors = ["#6b93ff", "#976fff", "#e46ace", "#ffb300", "#31b545"];
  return (
    <div className="pointer-events-none absolute inset-x-0 top-0 h-80 overflow-hidden" aria-hidden>
      {Array.from({ length: 28 }).map((_, i) => (
        <i key={i} className="confetti" style={{ left: `${(i * 37) % 100}%`, background: colors[i % colors.length], animationDelay: `${(i % 7) * 0.12}s` }} />
      ))}
    </div>
  );
}

export default function CheckoutPage() {
  const { id } = useParams<{ id: string }>();
  const { t } = useT();
  const router = useRouter();
  const qc = useQueryClient();
  const push = useToast((s) => s.push);
  const isTopup = id.startsWith("TP-");
  useBackButton(() => router.push(isTopup ? "/wallet" : "/orders"));
  const [tonConnectUI] = useTonConnectUI();
  const wallet = useTonWallet();
  const [busy, setBusy] = useState(false);
  const [manual, setManual] = useState(false);

  const order = useQuery({
    queryKey: ["order", id], enabled: !isTopup,
    queryFn: () => api.get<OrderDetail>(`/orders/${id}`),
    refetchInterval: (q) => (q.state.data && TERMINAL.includes(q.state.data.status) ? false : 3000),
  });
  const payId = isTopup ? id : order.data?.payments.find((p) => p.status === "pending")?.public_id ?? order.data?.payments.at(-1)?.public_id;
  const ins = useQuery({
    queryKey: ["ins", payId], enabled: !!payId,
    queryFn: () => api.get<PaymentInfo>(`/payments/${payId}/instructions`),
    refetchInterval: (q) => (isTopup && q.state.data?.status === "pending" ? 3000 : false),
  });
  const left = useCountdown(ins.data?.status === "pending" ? ins.data.expires_at : null);

  const status: OrderStatus | null = isTopup
    ? ins.data ? (ins.data.status === "confirmed" ? "completed" : ins.data.status === "expired" ? "expired" : "awaiting_payment") : null
    : order.data?.status ?? null;
  const done = status === "completed";
  useEffect(() => { if (done) { haptic("success"); qc.invalidateQueries({ queryKey: ["me"] }); } }, [done, qc]);
  useEffect(() => {
    const w = tg();
    if (status === "awaiting_payment") w?.enableClosingConfirmation();
    return () => w?.disableClosingConfirmation();
  }, [status]);

  if (order.error || ins.error) return <ErrorBox error={order.error ?? ins.error} onRetry={() => { order.refetch(); ins.refetch(); }} />;
  if (!status || !ins.data) return <div className="space-y-3"><Skeleton className="h-10 w-2/3" /><Skeleton className="h-40" /><Skeleton className="h-32" /></div>;

  const o = order.data;
  const p = ins.data;
  const stepIdx = status === "awaiting_payment" ? 0 : status === "paid" ? 1 : status === "processing" ? 2 : status === "completed" ? 3 : -1;
  const title = isTopup ? t("topup") : o!.product_type === "premium" ? `💎 Premium · ${t("months", { n: o!.plan_months! })}` : `⭐ Stars · ${num(o!.stars_amount!)}`;
  const expired = status === "awaiting_payment" && left === 0;

  const copy = async (text: string) => { try { await navigator.clipboard.writeText(text); push(t("copied")); } catch { /* clipboard blocked */ } };

  const sendTon = async () => {
    if (!p.address || !p.comment || !p.amount_nano) return;
    setBusy(true);
    try {
      const r = await tonConnectUI.sendTransaction({ validUntil: Math.floor(Date.now() / 1000) + 600, messages: [{ address: p.address, amount: p.amount_nano, payload: tonPayload(p.comment) }] });
      await api.post(`/payments/${p.payment_id}/ton/submitted`, { boc: r.boc }).catch(() => undefined);
      haptic("success");
    } catch (e) {
      push(t("pay_cancelled"), "err");
      void e;
    } finally { setBusy(false); }
  };

  const payStars = async () => {
    setBusy(true);
    try {
      const { invoice_link } = await api.post<{ invoice_link: string }>(`/payments/${p.payment_id}/stars-link`);
      const w = tg();
      if (w) w.openInvoice(invoice_link, (s) => { if (s === "paid") { haptic("success"); push(t("stars_paid")); order.refetch(); ins.refetch(); } else if (s === "cancelled") push(t("pay_cancelled"), "err"); });
      else window.open(invoice_link, "_blank");
    } catch (e) { push(e instanceof ApiError ? e.message : t("error_generic"), "err"); }
    finally { setBusy(false); }
  };

  const cancel = async () => {
    try { if (!isTopup) await api.post(`/orders/${id}/cancel`); router.push("/"); } catch { push(t("error_generic"), "err"); }
  };

  let action: { text: string; onClick: () => void; loading?: boolean; disabled?: boolean } | null = null;
  if (status === "awaiting_payment" && !expired) {
    if (p.method === "ton") action = wallet ? { text: t("confirm_wallet"), onClick: sendTon, loading: busy } : { text: t("connect_wallet"), onClick: () => tonConnectUI.openModal(), tone: undefined } as never;
    if (p.method === "stars") action = { text: t("pay_stars", { a: `${num(Number(p.amount))} ⭐` }), onClick: payStars, loading: busy };
  }
  const goHome = () => router.push("/");

  return (
    <div className="relative space-y-4">
      {done && <Confetti />}
      <PageHeader title={isTopup ? p.payment_id : o!.public_id} right={<StatusBadge status={status} />} />
      <div className="text-hint">{title}</div>

      {done ? (
        <Card className="relative space-y-2 py-8 text-center">
          <div className="pop text-6xl">🎉</div>
          <div className="text-[22px] font-bold">{t("done_title")}</div>
          <div className="text-hint">{t("done_sub")}</div>
        </Card>
      ) : status === "awaiting_payment" ? (
        <Card className="space-y-1 text-center">
          <div className="num text-[30px] font-bold leading-9" data-testid="amount">{p.method === "ton" ? `${fmtTon(p.amount)} TON` : p.method === "stars" ? `${num(Number(p.amount))} ⭐` : usd(isTopup ? p.amount : o!.price_usd)}</div>
          {o && <div className="num text-hint">≈ {usd(o.price_usd)}</div>}
          {isTopup && p.currency === "TON" && <div className="num text-hint">≈ {t("topup")}</div>}
          {left !== null && <div className={clsx("num font-medium", expired ? "text-danger" : "text-warning")}>⏳ {expired ? t("expired") : t("time_left", { t: mmss(left) })}</div>}
        </Card>
      ) : status === "needs_review" ? (
        <Card className="text-center text-hint">🔍 {t("review_note")}</Card>
      ) : status === "failed" || status === "refunded" ? (
        <Card className="text-center">❌ {t("failed_refund")}</Card>
      ) : (
        <Card className="text-center text-hint">{t(`st_${status}`)}</Card>
      )}

      {stepIdx >= 0 && (
        <Card className="space-y-3">
          {STEPS.map((s, i) => (
            <div key={s} className={clsx("flex items-center gap-3", i > stepIdx && "opacity-40")}>
              <span className={clsx("flex h-6 w-6 items-center justify-center rounded-full text-xs", i < stepIdx || done ? "bg-success text-white" : i === stepIdx ? "bg-accent text-white" : "bg-bg2")}>
                {i < stepIdx || done ? <Check size={14} /> : i === stepIdx ? <span className="h-2 w-2 animate-pulse rounded-full bg-white" /> : i + 1}
              </span>
              <span className={clsx(i === stepIdx && !done && "font-semibold")}>{t(`st_${s}`)}</span>
            </div>
          ))}
        </Card>
      )}

      {status === "awaiting_payment" && p.method === "ton" && p.address && (
        <Card className="space-y-2">
          <button className="flex w-full items-center justify-between font-medium" onClick={() => setManual(!manual)}>
            <span>{t("manual_pay")}</span>
            <ChevronDown size={18} className={clsx("transition", manual && "rotate-180")} />
          </button>
          {manual && (
            <div className="space-y-3 pt-1 text-sm">
              {([[t("address"), p.address], [t("comment"), p.comment!], ["TON", fmtTon(p.amount)]] as const).map(([k, v]) => (
                <div key={k} className="flex items-center justify-between gap-2">
                  <div className="min-w-0"><div className="text-xs text-hint">{k}</div><div className="break-all font-mono">{v}</div></div>
                  <button onClick={() => copy(v)} className="shrink-0 rounded-lg bg-bg2 p-2" aria-label="copy"><Copy size={16} /></button>
                </div>
              ))}
              {p.tonkeeper_link && <a href={p.tonkeeper_link} className="block text-accent underline">Tonkeeper</a>}
            </div>
          )}
        </Card>
      )}

      {done || status === "failed" || status === "refunded" || status === "expired" || status === "cancelled" || expired ? (
        <div className="flex gap-2">
          <Btn tone="soft" full onClick={goHome}>{t("home")}</Btn>
          <Btn tone="primary" full onClick={() => router.push(isTopup ? "/wallet" : o?.product_type === "stars" ? "/stars" : "/premium")}>{isTopup ? t("wallet") : t("buy_again")}</Btn>
        </div>
      ) : status === "awaiting_payment" ? (
        <Btn tone="danger" full onClick={cancel}>{t("cancel_order")}</Btn>
      ) : null}

      {action && <MainAction text={action.text} onClick={action.onClick} loading={action.loading} />}
    </div>
  );
}
