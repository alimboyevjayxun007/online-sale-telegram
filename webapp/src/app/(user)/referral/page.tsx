"use client";
import { useQuery } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { Btn, Card, Skeleton, useToast } from "@/components/ui";
import { PageHeader } from "@/components/Shell";
import { useBackButton } from "@/hooks/useBackButton";
import { api } from "@/lib/api";
import { usd } from "@/lib/format";
import { useT } from "@/lib/i18n";
import { shareLink } from "@/lib/tma";

export default function ReferralPage() {
  const { t } = useT();
  const router = useRouter();
  useBackButton(() => router.push("/profile"));
  const push = useToast((s) => s.push);
  const q = useQuery({ queryKey: ["referral"], queryFn: () => api.get<{ link: string | null; percent: string; invited: number; earned_usd: string }>("/referral") });
  if (!q.data) return <Skeleton className="h-48" />;
  const r = q.data;
  return (
    <div className="space-y-4">
      <PageHeader title={`👥 ${t("referral")}`} />
      <Card className="space-y-1 text-center"><div className="text-3xl">🎁</div><div className="font-semibold">{t("invite_sub", { p: r.percent })}</div></Card>
      {r.link && (
        <Card className="space-y-3">
          <div className="break-all rounded-xl bg-bg2 p-3 font-mono text-sm" data-testid="ref-link">{r.link}</div>
          <div className="flex gap-2">
            <Btn tone="success" full onClick={() => shareLink(r.link!, t("share_text"))}>{t("share")}</Btn>
            <Btn tone="soft" full onClick={async () => { await navigator.clipboard.writeText(r.link!).catch(() => undefined); push(t("copied")); }}>{t("copy_link")}</Btn>
          </div>
        </Card>
      )}
      <div className="grid grid-cols-2 gap-3">
        <Card className="text-center"><div className="num text-2xl font-bold">{r.invited}</div><div className="text-sm text-hint">{t("invited")}</div></Card>
        <Card className="text-center"><div className="num text-2xl font-bold">{usd(r.earned_usd)}</div><div className="text-sm text-hint">{t("earned")}</div></Card>
      </div>
    </div>
  );
}
