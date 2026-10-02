"use client";
import { useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { ChevronRight, HelpCircle, Users, FileText } from "lucide-react";
import { Card, Segmented } from "@/components/ui";
import { PageHeader } from "@/components/Shell";
import { useMe } from "@/hooks/queries";
import { api } from "@/lib/api";
import { useT, type Lang } from "@/lib/i18n";

export default function ProfilePage() {
  const { t, lang, setLang } = useT();
  const me = useMe();
  const qc = useQueryClient();
  const change = async (l: Lang) => { setLang(l); await api.patch("/me", { language: l }); qc.invalidateQueries({ queryKey: ["me"] }); };
  const link = (href: string, icon: React.ReactNode, label: string) => (
    <Link href={href} className="flex items-center justify-between px-4 py-3.5"><span className="flex items-center gap-3">{icon}{label}</span><ChevronRight size={18} className="text-hint" /></Link>
  );
  return (
    <div className="space-y-4">
      <PageHeader title={t("profile")} />
      <Card className="flex items-center gap-4">
        <div className="flex h-16 w-16 items-center justify-center rounded-full text-2xl font-bold text-white [background:var(--premium-gradient)]">{(me.data?.name ?? "?").slice(0, 1).toUpperCase()}</div>
        <div><div className="text-lg font-semibold">{me.data?.name}</div><div className="text-sm text-hint">{me.data?.username ? `@${me.data.username} · ` : ""}ID {me.data?.id}</div></div>
      </Card>
      <Card className="space-y-2">
        <div className="text-sm font-medium text-hint">{t("language")}</div>
        <Segmented value={lang} onChange={change} options={[{ value: "uz", label: "🇺🇿 UZ" }, { value: "ru", label: "🇷🇺 RU" }, { value: "en", label: "🇬🇧 EN" }]} />
      </Card>
      <Card className="divide-y divide-line !p-0">
        {link("/referral", <Users size={20} className="text-accent" />, t("referral"))}
        {link("/help", <HelpCircle size={20} className="text-accent" />, t("help"))}
        {link("/terms", <FileText size={20} className="text-accent" />, t("terms"))}
      </Card>
      {me.data?.is_admin && (
        <Link href="/admin" data-testid="admin-link"><div className="rounded-2xl p-4 text-center font-semibold text-white [background:var(--premium-gradient)]">{t("admin_panel")}</div></Link>
      )}
    </div>
  );
}
