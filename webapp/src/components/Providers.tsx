"use client";
import { QueryClient, QueryClientProvider, useQuery } from "@tanstack/react-query";
import { TonConnectUIProvider } from "@tonconnect/ui-react";
import { useEffect, useMemo, useState, type ReactNode } from "react";
import { api, type Me } from "@/lib/api";
import { I18nContext, makeT, type Lang } from "@/lib/i18n";
import { startParam, tg } from "@/lib/tma";
import { Toaster } from "./ui";
import { useRouter } from "next/navigation";

function applyTheme() {
  const w = tg();
  const root = document.documentElement;
  if (w) {
    root.dataset.scheme = w.colorScheme;
    for (const [k, v] of Object.entries(w.themeParams)) root.style.setProperty(`--tg-theme-${k.replaceAll("_", "-")}`, v);
  }
}

function I18nProvider({ children }: { children: ReactNode }) {
  const me = useQuery({ queryKey: ["me"], queryFn: () => api.get<Me>("/me"), staleTime: 10_000, retry: false });
  const [override, setOverride] = useState<Lang | null>(null);
  const initial = ((tg()?.initDataUnsafe.user?.language_code ?? "uz").slice(0, 2) as Lang);
  const lang: Lang = override ?? me.data?.language ?? (["uz", "ru", "en"].includes(initial) ? initial : "uz");
  const value = useMemo(() => ({ lang, setLang: setOverride, t: makeT(lang) }), [lang]);
  return <I18nContext.Provider value={value}>{children}</I18nContext.Provider>;
}

/** One-time Telegram bootstrap: ready/expand/theme + deep-link (startapp) routing. */
function Bootstrap() {
  const router = useRouter();
  useEffect(() => {
    const w = tg();
    w?.ready();
    w?.expand();
    w?.disableVerticalSwipes?.();
    applyTheme();
    w?.onEvent("themeChanged", applyTheme);
    const p = startParam();
    if (p && !sessionStorage.getItem("deeplinked")) {
      sessionStorage.setItem("deeplinked", "1");
      const map: Record<string, string> = { premium: "/premium", stars: "/stars", wallet: "/wallet", admin: "/admin", orders: "/orders", ref: "/referral" };
      if (map[p]) router.replace(map[p]);
    }
    return () => w?.offEvent("themeChanged", applyTheme);
  }, [router]);
  return null;
}

export function Providers({ children }: { children: ReactNode }) {
  const [qc] = useState(() => new QueryClient({ defaultOptions: { queries: { retry: 1, refetchOnWindowFocus: false } } }));
  const [origin, setOrigin] = useState("");
  useEffect(() => setOrigin(window.location.origin), []);
  const bot = process.env.NEXT_PUBLIC_BOT_USERNAME;
  const content = (
    <QueryClientProvider client={qc}>
      <I18nProvider>
        <Bootstrap />
        {children}
        <Toaster />
      </I18nProvider>
    </QueryClientProvider>
  );
  if (!origin) return content;
  return (
    <TonConnectUIProvider
      manifestUrl={`${origin}/tonconnect-manifest.json`}
      actionsConfiguration={bot ? { twaReturnUrl: `https://t.me/${bot}/app` as `${string}://${string}` } : undefined}
    >
      {content}
    </TonConnectUIProvider>
  );
}
