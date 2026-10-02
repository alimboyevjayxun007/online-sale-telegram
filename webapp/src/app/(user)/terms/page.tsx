"use client";
import { useRouter } from "next/navigation";
import { Card } from "@/components/ui";
import { PageHeader } from "@/components/Shell";
import { useBackButton } from "@/hooks/useBackButton";
import { useT } from "@/lib/i18n";

export default function TermsPage() {
  const { t } = useT();
  const router = useRouter();
  useBackButton(() => router.push("/profile"));
  return (
    <div className="space-y-4">
      <PageHeader title={t("terms")} />
      <Card><p className="leading-6 text-hint">{t("terms_body")}</p></Card>
    </div>
  );
}
