"use client";
import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { tg } from "@/lib/tma";

/** Shows Telegram's native BackButton for the lifetime of the page. */
export function useBackButton(onBack?: () => void) {
  const router = useRouter();
  useEffect(() => {
    const w = tg();
    if (!w?.initData) return;
    const handler = () => (onBack ? onBack() : router.back());
    w.BackButton.show();
    w.BackButton.onClick(handler);
    return () => {
      w.BackButton.offClick(handler);
      w.BackButton.hide();
    };
  }, [onBack, router]);
}
