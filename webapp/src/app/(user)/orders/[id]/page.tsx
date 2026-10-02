"use client";
import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { Btn, Card, ErrorBox, Skeleton, StatusBadge } from "@/components/ui";
import { PageHeader } from "@/components/Shell";
import { useBackButton } from "@/hooks/useBackButton";
import { useCatalog } from "@/hooks/queries";
import { api, type OrderDetail } from "@/lib/api";
import { num, usd, when } from "@/lib/format";
import { useT } from "@/lib/i18n";
import { openTgLink } from "@/lib/tma";

export default function OrderPage() {
  const { id } = useParams<{ id: string }>();
  const { t } = useT();
  const router = useRouter();
  useBackButton(() => router.push("/orders"));
  const cat = useCatalog();
  const q = useQuery({ queryKey: ["order", id], queryFn: () => api.get<OrderDetail>(`/orders/${id}`) });
  if (q.error) return <ErrorBox error={q.error} onRetry={() => q.refetch()} />;
  if (!q.data) return <Skeleton className="h-60" />;
  const o = q.data;
  const support = cat.data?.support_username;
  return (
    <div className="space-y-4">
      <PageHeader title={o.public_id} right={<StatusBadge status={o.status} />} />
      <Card className="space-y-2">
        <div className="text-lg font-semibold">{o.product_type === "premium" ? `💎 Premium · ${t("months", { n: o.plan_months! })}` : `⭐ Stars · ${num(o.stars_amount!)}`}</div>
        <div className="text-hint">→ {o.recipient_type === "self" ? t("for_me") : `@${o.recipient_username}`}</div>
        <div className="num flex justify-between"><span className="text-hint">{t("total")}</span><b>{usd(o.price_usd)}</b></div>
        {Number(o.discount_usd) > 0 && <div className="num flex justify-between text-success"><span>🎟</span><span>−{usd(o.discount_usd)}</span></div>}
        <div className="num flex justify-between text-sm text-hint"><span>{o.payment_method.toUpperCase()}</span><span>{o.price_amount} {o.price_currency}</span></div>
      </Card>
      <Card className="space-y-2">
        {o.events.map((e, i) => (
          <div key={i} className="flex justify-between text-sm"><span>{t(`st_${e.status}`)}</span><span className="text-hint">{when(e.at)}</span></div>
        ))}
      </Card>
      {o.status === "needs_review" && <Card className="text-center text-hint">🔍 {t("review_note")}</Card>}
      <div className="flex gap-2">
        <Link href={o.product_type === "premium" ? "/premium" : "/stars"} className="flex-1"><Btn tone="success" full>🔁 {t("repeat")}</Btn></Link>
        {support && ["failed", "needs_review", "refunded"].includes(o.status) && <Btn tone="soft" full onClick={() => openTgLink(`https://t.me/${support}`)}>🆘 {t("help_me")}</Btn>}
      </div>
    </div>
  );
}
