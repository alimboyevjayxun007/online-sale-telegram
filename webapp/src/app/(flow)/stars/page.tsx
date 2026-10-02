"use client";
import clsx from "clsx";
import { useRouter } from "next/navigation";
import { useEffect, useMemo, useState } from "react";
import { MainAction } from "@/components/MainAction";
import { PageHeader } from "@/components/Shell";
import { Hero, MethodPicker, PromoBox, RecipientPicker, type Method, type PromoState, type Recipient } from "@/components/shop/parts";
import { Card, ErrorBox, Price, Section, Skeleton, inputCls, useToast } from "@/components/ui";
import { useBackButton } from "@/hooks/useBackButton";
import { useCatalog, useMe } from "@/hooks/queries";
import { api, ApiError, newKey } from "@/lib/api";
import { num, ton as fmtTon, usd, uzs } from "@/lib/format";
import { useT } from "@/lib/i18n";
import { haptic } from "@/lib/tma";

export default function StarsPage() {
  const { t } = useT();
  const router = useRouter();
  const push = useToast((s) => s.push);
  useBackButton(() => router.push("/"));
  const me = useMe();
  const cat = useCatalog();
  const [amount, setAmount] = useState<number | null>(null);
  const [custom, setCustom] = useState("");
  const [rec, setRec] = useState<Recipient>({ type: "self", username: "", ok: false });
  const [method, setMethod] = useState<Method>("ton");
  const [promo, setPromo] = useState<PromoState | null>(null);
  const [quote, setQuote] = useState<{ price_usd: string; price_ton: string; price_uzs: number } | null>(null);
  const [busy, setBusy] = useState(false);
  const key = useMemo(() => newKey(), [amount, method, rec.username, rec.type, promo?.code]); // eslint-disable-line react-hooks/exhaustive-deps

  // self recipient is only valid when the user has a username
  useEffect(() => { if (me.data && rec.type === "self") setRec((r) => ({ ...r, ok: !!me.data!.username })); }, [me.data, rec.type]);
  useEffect(() => {
    if (!amount || amount < 50) { setQuote(null); return; }
    const id = setTimeout(() => api.post<typeof quote>("/catalog/stars-quote", { amount }).then(setQuote).catch(() => setQuote(null)), 250);
    return () => clearTimeout(id);
  }, [amount]);

  if (cat.error) return <ErrorBox error={cat.error} onRetry={() => cat.refetch()} />;
  if (!me.data || !cat.data) return <div className="space-y-3"><Skeleton className="h-28" /><Skeleton className="h-40" /></div>;

  const max = cat.data.stars_max;
  const valid = !!amount && amount >= 50 && amount <= max;
  const price = quote ? (promo?.final ?? Number(quote.price_usd)) : 0;
  const tonUsd = Number(cat.data.rates.ton_usd);
  const priceTon = quote ? (promo ? Math.ceil((price / tonUsd) * 100) / 100 : Number(quote.price_ton)) : 0;
  const balance = Number(me.data.balance_usd);
  const m = cat.data.methods;
  const options = [
    ...(m.ton ? [{ method: "ton" as const, label: `💎 ${t("m_ton")}`, sub: quote ? `${fmtTon(priceTon)} TON` : "—" }] : []),
    ...(m.balance ? [{ method: "balance" as const, label: `💼 ${t("m_balance")}`, sub: usd(balance), disabled: !!quote && balance < price, note: quote && balance < price ? t("balance_low") : undefined }] : []),
  ];
  const label = method === "ton" ? t("pay_ton", { a: fmtTon(priceTon) }) : t("pay_balance", { a: usd(price) });
  const pick = (a: number) => { haptic("select"); setAmount(a); setCustom(""); };

  const submit = async () => {
    if (!valid) return;
    setBusy(true);
    try {
      const r = await api.post<{ order: { public_id: string } }>(
        "/orders",
        { product_type: "stars", stars_amount: amount, payment_method: method, promo_code: promo?.code, recipient: { type: rec.type, username: rec.type === "other" ? rec.username : undefined, name: rec.name } },
        key,
      );
      router.push(`/checkout/${r.order.public_id}`);
    } catch (e) {
      push(e instanceof ApiError ? (t(`err_${e.code}`) !== `err_${e.code}` ? t(`err_${e.code}`) : e.message) : t("error_generic"), "err");
      setBusy(false);
    }
  };

  return (
    <div className="space-y-4">
      <PageHeader title={t("tg_stars")} />
      <Hero kind="stars" title={t("tg_stars")} sub={t("min50")} />
      <RecipientPicker me={me.data} product="stars" value={rec} onChange={setRec} />
      <Section title={`2 · ${t("amount")}`}>
        <div className="grid grid-cols-3 gap-2">
          {cat.data.star_packages.map((p) => (
            <button key={p.id} onClick={() => pick(p.amount)} data-testid={`pkg-${p.amount}`}
              className={clsx("rounded-2xl bg-surface p-3 text-center", amount === p.amount && !custom ? "ring-2 ring-accent" : "ring-1 ring-line")}>
              <div className="font-bold">{p.popular && "🔥"}⭐ {num(p.amount)}</div>
              <div className="num text-xs text-hint">{usd(p.price_usd)}</div>
            </button>
          ))}
        </div>
        <div className="flex items-center gap-2">
          <input className={inputCls} inputMode="numeric" placeholder={`${t("custom_amount")} (50–${num(max)})`} value={custom} data-testid="stars-custom"
            onChange={(e) => { const v = e.target.value.replace(/\D/g, ""); setCustom(v); setAmount(v ? Number(v) : null); }} />
          <span className="text-xl">⭐</span>
        </div>
        {custom && !valid && <div className="px-1 text-sm text-danger">{t("min50")}</div>}
      </Section>
      <MethodPicker step={3} value={method} onChange={setMethod} options={options} />
      <PromoBox product="stars" stars={valid ? amount! : undefined} value={promo} onChange={setPromo} />
      {quote && valid && (
        <Card className="flex items-end justify-between">
          <span className="text-hint">{t("total")}</span>
          <Price big usd={usd(price)} sub={uzs(price * Number(cat.data.rates.usd_uzs))} />
        </Card>
      )}
      <MainAction text={label} disabled={!valid || !quote || !rec.ok} loading={busy} onClick={submit} />
    </div>
  );
}
