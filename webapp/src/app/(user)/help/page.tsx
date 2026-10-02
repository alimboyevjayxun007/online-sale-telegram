"use client";
import { ChevronDown } from "lucide-react";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { Btn, Card } from "@/components/ui";
import { PageHeader } from "@/components/Shell";
import { useBackButton } from "@/hooks/useBackButton";
import { useCatalog } from "@/hooks/queries";
import { useT } from "@/lib/i18n";
import { openTgLink } from "@/lib/tma";

export default function HelpPage() {
  const { t } = useT();
  const router = useRouter();
  useBackButton(() => router.push("/profile"));
  const [open, setOpen] = useState<number | null>(0);
  const support = useCatalog().data?.support_username;
  return (
    <div className="space-y-4">
      <PageHeader title={`🆘 ${t("help")}`} />
      <Card className="divide-y divide-line !p-0">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="px-4 py-3">
            <button className="flex w-full items-center justify-between gap-2 text-left font-medium" onClick={() => setOpen(open === i - 1 ? null : i - 1)}>
              {t(`faq${i}q`)}<ChevronDown size={18} className={open === i - 1 ? "rotate-180 transition" : "transition"} />
            </button>
            {open === i - 1 && <p className="pt-2 text-hint">{t(`faq${i}a`)}</p>}
          </div>
        ))}
      </Card>
      {support && <Btn tone="primary" full onClick={() => openTgLink(`https://t.me/${support}`)}>💬 {t("contact_support")}</Btn>}
    </div>
  );
}
