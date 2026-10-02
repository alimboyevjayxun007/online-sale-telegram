"use client";
import clsx from "clsx";
import { useRouter } from "next/navigation";
import { useMemo, useState } from "react";
import { MainAction } from "@/components/MainAction";
import { PageHeader } from "@/components/Shell";
import { Hero, MethodPicker, PromoBox, RecipientPicker, type Method, type PromoState, type Recipient } from "@/components/shop/parts";
import { Card, ErrorBox, Price, Section, Skeleton, useToast } from "@/components/ui";
import { useBackButton } from "@/hooks/useBackButton";
import { useCatalog, useMe } from "@/hooks/queries";
import { api, ApiError, newKey } from "@/lib/api";
import { num, ton as fmtTon, usd, uzs } from "@/lib/format";
import { useT } from "@/lib/i18n";
import { haptic } from "@/lib/tma";

export default function PremiumPage() {
  const { t } = useT();
  const router = useRouter();
  const push = useToast((s) => s.push);
  useBackButton(() => router.push("/"));
  const me = useMe();
  const cat = useCatalog();
  const [planId, setPlanId] = useState<number | null>(null);
  const [rec, setRec] = useState<Recipient>({ type: "self", username: "", ok: true });
  const [method, setMethod] = useState<Method>("ton");
  const [promo, setPromo] = useState<PromoState | null>(null);
  const [busy, setBusy] = useState(false);
  const key = useMemo(() => newKey(), [planId, method, rec.username, rec.type, promo?.code]); // eslint-disable-line react-hooks/exhaustive-deps

  if (cat.error) return <ErrorBox error={cat.error} onRetry={() => cat.refetch()} />;
  if (!me.data || !cat.data) return <div className="space-y-3"><Skeleton className="h-28" /><Skeleton className="h-40" /></div>;

  const plans = cat.data.plans;
  const plan = plans.find((p) => p.id === planId && p.available);
  const price = plan ? (promo?.final ?? Number(plan.price_usd)) : 0;
  const tonUsd = Number(cat.data.rates.ton_usd);
  const priceTon = plan ? (promo ? Math.ceil((price / tonUsd) * 100) / 100 : Number(plan.price_ton)) : 0;
  const stars = plan?.price_xtr ?? 0;
  const balance = Number(me.data.balance_usd);
  const m = cat.data.methods;
  const options = [
    ...(m.ton ? [{ method: "ton" as const, label: `💎 ${t("m_ton")}`, sub: plan ? `${fmtTon(priceTon)} TON` : "—" }] : []),
    ...(m.stars ? [{ method: "stars" as const, label: `⭐ ${t("m_stars")}`, sub: plan ? `${num(stars)} ⭐` : "—" }] : []),
    ...(m.balance ? [{ method: "balance" as const, label: `💼 ${t("m_balance")}`, sub: `${usd(balance)}`, disabled: !!plan && balance < price, note: plan && balance < price ? t("balance_low") : undefined }] : []),
  ];
  const noUser = rec.type === "self" ? !me.data.username : false;
  const ready = !!plan && rec.ok && !(noUser && method !== "stars");
  const label = method === "ton" ? t("pay_ton", { a: fmtTon(priceTon) }) : method === "stars" ? t("pay_stars", { a: `${num(stars)} ⭐` }) : t("pay_balance", { a: usd(price) });

  const submit = async () => {
    if (!plan) return;
    setBusy(true);
    try {
      const r = await api.post<{ order: { public_id: string } }>(
        "/orders",
        { product_type: "premium", plan_id: plan.id, payment_method: method, promo_code: promo?.code, recipient: { type: rec.type, username: rec.type === "other" ? rec.username : undefined, name: rec.name } },
        key,
      );
      haptic("success");
      router.push(`/checkout/${r.order.public_id}`);
    } catch (e) {
      push(e instanceof ApiError ? (t(`err_${e.code}`) !== `err_${e.code}` ? t(`err_${e.code}`) : e.message) : t("error_generic"), "err");
      setBusy(false);
    }
  };

  return (
    <div className="space-y-4">
      <PageHeader title={t("tg_premium")} />
      <Hero kind="premium" title={t("tg_premium")} sub={t("cheaper")} />
      <RecipientPicker me={me.data} product="premium" months={plan?.months} value={rec} onChange={setRec} />
      <Section title={`2 · ${t("duration")}`}>
        <Card className="divide-y divide-line !p-0" >
          {plans.map((p) => {
            const sel = p.id === planId;
            const disabled = !p.available;
            return (
              <button key={p.id} disabled={disabled} onClick={() => { haptic("select"); setPlanId(p.id); }} data-testid={`plan-${p.months}`}
                className={clsx("flex w-full items-center justify-between gap-3 px-4 py-3 text-left", sel && "bg-accent/10 ring-2 ring-inset ring-accent", disabled && "opacity-50")}>
                <div>
                  <div className="font-semibold">{t("months", { n: p.months })} {p.badge && <span className="ml-1 text-xs text-accent">{p.badge} {t("best")}</span>}</div>
                  {p.available ? <div className="num text-xs text-hint">{fmtTon(p.price_ton!)} TON · {num(p.price_xtr!)} ⭐ · {uzs(p.price_uzs!)}</div> : <div className="text-xs text-hint">{t("soon")}</div>}
                </div>
                {p.available && <Price usd={usd(p.price_usd!)} sub={p.saving_pct ? `−${p.saving_pct}%` : undefined} />}
              </button>
            );
          })}
        </Card>
      </Section>
      <MethodPicker step={3} value={method} onChange={setMethod} options={options} />
      <PromoBox product="premium" planId={plan?.id} value={promo} onChange={setPromo} />
      {plan && (
        <Card className="flex items-end justify-between">
          <span className="text-hint">{t("total")}</span>
          <Price big usd={usd(price)} sub={uzs(price * Number(cat.data.rates.usd_uzs))} />
        </Card>
      )}
      <MainAction text={label} disabled={!ready} loading={busy} onClick={submit} />
    </div>
  );
}
