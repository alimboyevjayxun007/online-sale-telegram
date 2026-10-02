export const usd = (v: string | number) => `${Number(v).toFixed(2)} $`;
export const uzs = (v: number) => `${Math.round(v).toString().replace(/\B(?=(\d{3})+(?!\d))/g, " ")} so'm`;
export const ton = (v: string | number) => Number(v).toFixed(2);
export const num = (v: number) => Math.round(v).toString().replace(/\B(?=(\d{3})+(?!\d))/g, " ");
export const when = (iso: string) =>
  new Date(iso).toLocaleString("uz-UZ", { day: "2-digit", month: "2-digit", year: "numeric", hour: "2-digit", minute: "2-digit", timeZone: "Asia/Tashkent" });
export const pct = (v: number | null | undefined) => (v === null || v === undefined ? "" : `${v >= 0 ? "▲" : "▼"} ${Math.abs(v).toFixed(0)}%`);
