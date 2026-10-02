import { AuthGate } from "@/components/Shell";
import { BottomNav } from "@/components/Nav";

export default function UserLayout({ children }: { children: React.ReactNode }) {
  return (
    <AuthGate>
      <main className="mx-auto min-h-screen max-w-md space-y-4 p-4 pb-24">{children}</main>
      <BottomNav />
    </AuthGate>
  );
}
