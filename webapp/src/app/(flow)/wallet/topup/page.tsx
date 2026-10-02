"use client";
import clsx from "clsx";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { MainAction } from "@/components/MainAction";
import { PageHeader } from "@/components/Shell";
import { Section, Segmented, inputCls, useToast, Card } from "@/components/ui";
import { useBackButton } from "@/hooks/useBackButton";
import { useCatalog } from "@/hooks/queries";
import { api, ApiError } from "@/lib/api";
import { usd } from "@/lib/format";
import { useT } from "@/lib/i18n";
import { haptic } from "@/lib/tma";

export default function TopupPage() {
  const { t } = useT();
  const router = useRouter();
  useBackButton(() => router.push("/wallet"));
  const push = useToast((s) => s.push);
  const cat = useCatalog();
  const [method, setMethod] = useState<"ton" | "stars">("ton");
  const [amount, setAmount] = useState<number | null>(10);
  const [custom, setCustom] = useState("");
  const [busy, setBusy] = useState(false);
  const methods = [...(cat.data?.methods.ton ? [{ value: "ton" as const, label: "💎 TON" }] : []), ...(cat.data?.methods.topup_stars ? [{ value: "stars" as const, label: "⭐ Stars" }] : [])];
  const valid = !!amount && amount >= 1 && amount <= 5000;
  const submit = async () => {
    setBusy(true);
    try {
      const r = await api.post<{ payment_instructions: { payment_id: string } }>("/wallet/topup", { amount_usd: String(amount), method });
      router.push(`/checkout/${r.payment_instructions.payment_id}`);
    } catch (e) { push(e instanceof ApiError ? (t(`err_${e.code}`) !== `err_${e.code}` ? t(`err_${e.code}`) : e.message) : t("error_generic"), "err"); setBusy(false); }
  };
  return (
    <div className="space-y-4">
      <PageHeader title={t("topup")} />
      <Section title={t("topup_method")}>
        {methods.length > 0 ? <Segmented value={method} options={methods} onChange={setMethod} /> : <Card className="text-hint">—</Card>}
      </Section>
      <Section title={t("topup_amount")}>
        <div className="grid grid-cols-3 gap-2">
          {[5, 10, 25, 50, 100].map((a) => (
            <button key={a} data-testid={`amt-${a}`} onClick={() => { haptic("select"); setAmount(a); setCustom(""); }}
              className={clsx("rounded-2xl bg-surface p-3 text-center font-bold", amount === a && !custom ? "ring-2 ring-accent" : "ring-1 ring-line")}>{a} $</button>
          ))}
          <input className={clsx(inputCls, "text-center")} inputMode="decimal" placeholder="$" value={custom} data-testid="amt-custom"
            onChange={(e) => { const v = e.target.value.replace(/[^\d.]/g, ""); setCustom(v); setAmount(v ? Number(v) : null); }} />
        </div>
      </Section>
      <MainAction text={`${t("pay_topup")} ${valid ? usd(amount!) : ""}`} disabled={!valid || methods.length === 0} loading={busy} onClick={submit} />
    </div>
  );
}
