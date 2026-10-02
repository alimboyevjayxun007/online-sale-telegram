"use client";
import { useQuery } from "@tanstack/react-query";
import { useTonConnectUI, useTonWallet } from "@tonconnect/ui-react";
import Link from "next/link";
import { Card, Empty, Section, Skeleton } from "@/components/ui";
import { PageHeader } from "@/components/Shell";
import { useMe } from "@/hooks/queries";
import { api } from "@/lib/api";
import { usd, uzs, when } from "@/lib/format";
import { useT } from "@/lib/i18n";

interface Tx { amount_usd: string; type: string; at: string; balance_after: string }

export default function WalletPage() {
  const { t } = useT();
  const me = useMe();
  const tx = useQuery({ queryKey: ["wallet-tx"], queryFn: () => api.get<{ items: Tx[] }>("/wallet/transactions?limit=30") });
  const wallet = useTonWallet();
  const [ui] = useTonConnectUI();
  return (
    <div className="space-y-4">
      <PageHeader title={t("wallet")} />
      <Card className="space-y-2 !bg-[image:var(--premium-gradient)] text-white">
        <div className="text-sm opacity-90">💼 {t("balance")}</div>
        <div className="num text-[32px] font-bold leading-9" data-testid="wallet-balance">{me.data ? usd(me.data.balance_usd) : "—"}</div>
        <div className="num text-sm opacity-90">{me.data ? `≈ ${uzs(me.data.balance_uzs)} · ≈ ${me.data.balance_ton} TON` : ""}</div>
        <Link href="/wallet/topup" className="mt-2 block rounded-xl bg-white/25 py-2.5 text-center font-semibold" data-testid="topup-link">➕ {t("topup")}</Link>
      </Card>
      <Card className="flex items-center justify-between text-sm">
        <span>💎 TON {wallet ? `· ${wallet.account.address.slice(0, 4)}…${wallet.account.address.slice(-4)}` : ""}</span>
        <button className="font-semibold text-accent" onClick={() => (wallet ? ui.disconnect() : ui.openModal())}>{wallet ? "✕" : t("connect_wallet")}</button>
      </Card>
      <Section title={t("transactions")}>
        <Card className="divide-y divide-line !p-0">
          {tx.isLoading && <div className="p-4"><Skeleton /></div>}
          {tx.data?.items.length === 0 && <Empty icon="🧾" text={t("no_tx")} />}
          {tx.data?.items.map((r, i) => {
            const plus = Number(r.amount_usd) > 0;
            return (
              <div key={i} className="flex items-center justify-between px-4 py-3">
                <div><div className="font-medium">{r.type.replaceAll("_", " ")}</div><div className="text-xs text-hint">{when(r.at)}</div></div>
                <div className={`num font-semibold ${plus ? "text-success" : "text-danger"}`}>{plus ? "+" : "−"}{usd(Math.abs(Number(r.amount_usd)))}</div>
              </div>
            );
          })}
        </Card>
      </Section>
    </div>
  );
}
