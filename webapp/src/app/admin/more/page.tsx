"use client";
import Link from "next/link";
import { ChevronRight } from "lucide-react";
import { Card } from "@/components/ui";
import { PageHeader } from "@/components/Shell";
import { useMe } from "@/hooks/queries";

export default function More() {
  const role = useMe().data?.role;
  const items = [
    ["/admin/stats", "📊 Statistika", "admin"], ["/admin/pricing", "🏷 Narxlar", "admin"], ["/admin/broadcasts", "📣 Xabar yuborish", "admin"],
    ["/admin/promo", "🎟 Promokodlar", "admin"], ["/admin/settings", "⚙️ Sozlamalar", "admin"], ["/admin/admins", "👮 Adminlar", "owner"], ["/admin/audit", "🧾 Audit log", "admin"],
  ].filter(([, , need]) => need === "admin" ? role !== "support" : role === "owner");
  return (
    <div className="space-y-4">
      <PageHeader title="Ko'proq" />
      <Card className="divide-y divide-line !p-0">
        {items.map(([href, label]) => (
          <Link key={href} href={href} className="flex items-center justify-between px-4 py-3.5"><span>{label}</span><ChevronRight size={18} className="text-hint" /></Link>
        ))}
      </Card>
    </div>
  );
}
