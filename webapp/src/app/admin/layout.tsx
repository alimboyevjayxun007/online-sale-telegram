"use client";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect } from "react";
import { AdminNav } from "@/components/Nav";
import { AuthGate } from "@/components/Shell";
import { Skeleton } from "@/components/ui";
import { useMe } from "@/hooks/queries";

function Guard({ children }: { children: React.ReactNode }) {
  const me = useMe();
  const router = useRouter();
  useEffect(() => { if (me.data && !me.data.is_admin) router.replace("/"); }, [me.data, router]);
  if (!me.data?.is_admin) return <div className="p-4"><Skeleton className="h-40" /></div>;
  return (
    <>
      <main className="mx-auto min-h-screen max-w-2xl space-y-4 p-4 pb-24">
        <Link href="/" className="text-sm text-accent">← Foydalanuvchi rejimi · {me.data.role}</Link>
        {children}
      </main>
      <AdminNav />
    </>
  );
}

export default function AdminLayout({ children }: { children: React.ReactNode }) {
  return <AuthGate><Guard>{children}</Guard></AuthGate>;
}
