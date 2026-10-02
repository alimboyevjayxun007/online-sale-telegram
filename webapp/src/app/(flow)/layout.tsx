import { AuthGate } from "@/components/Shell";

export default function FlowLayout({ children }: { children: React.ReactNode }) {
  return (
    <AuthGate>
      <main className="mx-auto min-h-screen max-w-md space-y-4 p-4">{children}</main>
    </AuthGate>
  );
}
