"use client";
import { useEffect, useRef, useState } from "react";
import { Btn } from "./ui";
import { haptic, tg } from "@/lib/tma";

interface Props { text: string; onClick: () => void; disabled?: boolean; loading?: boolean; tone?: "success" | "primary" | "danger" }

/** Telegram's native MainButton inside Telegram; a sticky bottom button in a plain browser (dev / tests). */
export function MainAction({ text, onClick, disabled, loading, tone = "success" }: Props) {
  const [native, setNative] = useState(false);
  const cb = useRef(onClick);
  cb.current = onClick;

  useEffect(() => {
    const w = tg();
    if (!w?.initData) return;
    setNative(true);
    const handler = () => { haptic("tap"); cb.current(); };
    const color = tone === "success" ? "#31b545" : tone === "danger" ? "#e5484d" : w.themeParams.button_color || "#2481cc";
    w.MainButton.setParams({ text, color, text_color: "#ffffff", is_active: !disabled && !loading, is_visible: true });
    w.MainButton.onClick(handler);
    if (loading) w.MainButton.showProgress(true);
    else w.MainButton.hideProgress();
    return () => {
      w.MainButton.offClick(handler);
      w.MainButton.hideProgress();
      w.MainButton.hide();
    };
  }, [text, disabled, loading, tone]);

  return (
    <>
      <div className="h-24" />
      {!native && (
        <div className="safe-bottom fixed inset-x-0 bottom-0 z-30 border-t border-line bg-bg/95 px-4 pt-3 backdrop-blur">
          <Btn tone={tone === "danger" ? "danger" : tone} full disabled={disabled} loading={loading} onClick={onClick} data-testid="main-action">
            {text}
          </Btn>
        </div>
      )}
    </>
  );
}
