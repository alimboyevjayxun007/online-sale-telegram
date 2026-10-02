import { initDataRaw } from "./tma";

export class ApiError extends Error {
  constructor(public status: number, public code: string, message: string, public details?: Record<string, unknown>) {
    super(message);
  }
}

const BASE = process.env.NEXT_PUBLIC_API_BASE ?? "/api";

async function request<T>(method: string, path: string, body?: unknown, extra?: Record<string, string>): Promise<T> {
  const res = await fetch(`${BASE}/v1${path}`, {
    method,
    headers: {
      "Content-Type": "application/json",
      Authorization: `tma ${initDataRaw()}`,
      ...extra,
    },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  if (!res.ok) {
    let code = "ERROR";
    let message = res.statusText;
    let details: Record<string, unknown> | undefined;
    try {
      const j = await res.json();
      code = j.error?.code ?? code;
      message = j.error?.message ?? message;
      details = j.error?.details;
    } catch {
      /* non-JSON error */
    }
    throw new ApiError(res.status, code, message, details);
  }
  if (res.headers.get("content-type")?.includes("application/json")) return (await res.json()) as T;
  return undefined as T;
}

export const api = {
  get: <T>(path: string) => request<T>("GET", path),
  post: <T>(path: string, body?: unknown, idempotencyKey?: string) =>
    request<T>("POST", path, body ?? {}, idempotencyKey ? { "Idempotency-Key": idempotencyKey } : undefined),
  put: <T>(path: string, body?: unknown) => request<T>("PUT", path, body ?? {}),
  patch: <T>(path: string, body?: unknown) => request<T>("PATCH", path, body ?? {}),
  del: <T>(path: string) => request<T>("DELETE", path),
};

export const newKey = () => (typeof crypto !== "undefined" && "randomUUID" in crypto ? crypto.randomUUID() : String(Date.now()) + Math.random());

/* ---------- response types ---------- */
export interface Me {
  id: number; name: string | null; username: string | null; language: "uz" | "ru" | "en";
  balance_usd: string; balance_uzs: number; balance_ton: string; is_admin: boolean;
  role: "owner" | "admin" | "support" | null; ref_link: string | null;
}
export interface Plan {
  id: number; months: number; badge: string | null; available: boolean; coming_soon: boolean;
  price_usd?: string; price_ton?: string; price_xtr?: number; price_uzs?: number; saving_pct?: number;
}
export interface StarPackage { id: number; amount: number; popular: boolean; price_usd: string; price_ton: string; price_uzs: number }
export interface Catalog {
  plans: Plan[]; star_packages: StarPackage[];
  methods: { ton: boolean; stars: boolean; balance: boolean; topup_stars: boolean };
  rates: { ton_usd: string; usd_uzs: string }; stars_max: number; support_username: string;
}
export interface Order {
  public_id: string; product_type: "premium" | "stars"; plan_months: number | null; stars_amount: number | null;
  recipient_type: "self" | "other"; recipient_username: string | null; recipient_name: string | null;
  status: OrderStatus; payment_method: "ton" | "stars" | "balance"; price_usd: string; discount_usd: string;
  price_amount: string | null; price_currency: string | null; created_at: string; completed_at: string | null; error_code: string | null;
}
export type OrderStatus = "awaiting_payment" | "paid" | "processing" | "completed" | "failed" | "needs_review" | "refunded" | "expired" | "cancelled";
export interface PaymentInfo {
  payment_id: string; method: "ton" | "stars" | "balance"; amount: string; currency: string; expires_at: string | null;
  status?: string; purpose?: string; address?: string; amount_nano?: string; comment?: string; tonkeeper_link?: string;
}
export interface OrderDetail extends Order {
  events: { status: OrderStatus; at: string }[];
  payments: { public_id: string; method: string; status: string; amount: string; currency: string; expires_at: string | null }[];
}
