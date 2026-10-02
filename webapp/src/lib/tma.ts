/* Thin typed wrapper around Telegram.WebApp (loaded by the official script in layout.tsx). */

type HapticStyle = "light" | "medium" | "heavy" | "rigid" | "soft";
interface TgButton {
  text: string;
  color: string;
  textColor: string;
  isVisible: boolean;
  isActive: boolean;
  setParams(p: { text?: string; color?: string; text_color?: string; is_active?: boolean; is_visible?: boolean }): void;
  show(): void;
  hide(): void;
  onClick(cb: () => void): void;
  offClick(cb: () => void): void;
  showProgress(leave?: boolean): void;
  hideProgress(): void;
}
export interface TgWebApp {
  initData: string;
  initDataUnsafe: { user?: { id: number; first_name?: string; language_code?: string } ; start_param?: string };
  colorScheme: "light" | "dark";
  themeParams: Record<string, string>;
  platform: string;
  ready(): void;
  expand(): void;
  close(): void;
  setHeaderColor?(c: string): void;
  enableClosingConfirmation(): void;
  disableClosingConfirmation(): void;
  disableVerticalSwipes?(): void;
  MainButton: TgButton;
  BackButton: { show(): void; hide(): void; onClick(cb: () => void): void; offClick(cb: () => void): void };
  HapticFeedback: { impactOccurred(s: HapticStyle): void; notificationOccurred(t: "error" | "success" | "warning"): void; selectionChanged(): void };
  openInvoice(url: string, cb?: (status: "paid" | "cancelled" | "failed" | "pending") => void): void;
  openTelegramLink(url: string): void;
  openLink(url: string): void;
  showPopup?(p: { title?: string; message: string; buttons?: { id?: string; type?: string; text?: string }[] }, cb?: (id: string) => void): void;
  onEvent(name: string, cb: () => void): void;
  offEvent(name: string, cb: () => void): void;
}

declare global {
  interface Window {
    Telegram?: { WebApp: TgWebApp };
  }
}

export const tg = (): TgWebApp | undefined => (typeof window === "undefined" ? undefined : window.Telegram?.WebApp);
export const inTelegram = (): boolean => Boolean(tg()?.initData);

export function initDataRaw(): string {
  const real = tg()?.initData;
  if (real) return real;
  if (typeof window !== "undefined" && process.env.NODE_ENV !== "production") {
    try {
      return window.localStorage.getItem("devInitData") ?? process.env.NEXT_PUBLIC_DEV_INIT_DATA ?? "";
    } catch {
      return "";
    }
  }
  return "";
}

export function haptic(kind: "tap" | "select" | "success" | "error" | "warning" = "tap") {
  const h = tg()?.HapticFeedback;
  if (!h) return;
  if (kind === "tap") h.impactOccurred("light");
  else if (kind === "select") h.selectionChanged();
  else h.notificationOccurred(kind);
}

export function openTgLink(url: string) {
  const w = tg();
  if (w) w.openTelegramLink(url);
  else window.open(url, "_blank");
}

export function shareLink(link: string, text: string) {
  openTgLink(`https://t.me/share/url?url=${encodeURIComponent(link)}&text=${encodeURIComponent(text)}`);
}

export function startParam(): string | undefined {
  return tg()?.initDataUnsafe?.start_param ?? (typeof window !== "undefined" ? new URLSearchParams(window.location.search).get("startapp") ?? undefined : undefined);
}
