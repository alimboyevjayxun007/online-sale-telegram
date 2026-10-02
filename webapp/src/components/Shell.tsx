"use client";
import type { ReactNode } from "react";
import { useMe } from "@/hooks/queries";
import { ApiError } from "@/lib/api";
import { useT } from "@/lib/i18n";
import { Card, Skeleton } from "./ui";

/** Waits for authentication; shows friendly screens for expired sessions and maintenance. */
export function AuthGate({ children }: { children: ReactNode }) {
  const me = useMe();
  const { t } = useT();
  if (me.isLoading) {
    return (
      <div className="space-y-3 p-4" data-testid="auth-loading">
        <Skeleton className="h-8 w-1/2" />
        <Skeleton className="h-28" />
        <Skeleton className="h-28" />
      </div>
    );
  }
  if (me.error) {
    const e = me.error as ApiError;
    return (
      <div className="p-4">
        <Card className="space-y-2 text-center">
          <div className="text-4xl">{e.code === "MAINTENANCE" ? "🛠" : "🔒"}</div>
          <div className="font-semibold">{t(`err_${e.code}`) !== `err_${e.code}` ? t(`err_${e.code}`) : t("reopen")}</div>
          <div className="text-sm text-hint">{t("reopen")}</div>
        </Card>
      </div>
    );
  }
  return <>{children}</>;
}

export function PageHeader({ title, right }: { title: string; right?: ReactNode }) {
  return (
    <header className="flex items-center justify-between px-1 pb-1 pt-1">
      <h1 className="text-[22px] font-bold leading-7">{title}</h1>
      {right}
    </header>
  );
}
