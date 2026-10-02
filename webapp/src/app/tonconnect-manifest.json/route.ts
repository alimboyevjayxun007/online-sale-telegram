import { NextResponse } from "next/server";

export const dynamic = "force-dynamic";

export function GET(req: Request) {
  const url = process.env.NEXT_PUBLIC_APP_URL ?? new URL(req.url).origin;
  return NextResponse.json({ url, name: "Soft-tg-Market", iconUrl: `${url}/icons/icon-180.png` });
}
