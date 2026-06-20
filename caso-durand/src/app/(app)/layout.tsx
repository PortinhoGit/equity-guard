import { redirect } from "next/navigation";
import { LogOut } from "lucide-react";
import { auth } from "@/auth";
import { Sidebar } from "@/components/Sidebar";
import { Badge } from "@/components/ui";
import { sair } from "@/lib/auth-actions";

// Toda a área autenticada é dinâmica: dados consultados ao vivo a cada acesso.
export const dynamic = "force-dynamic";

export default async function AppLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const session = await auth();
  if (!session?.user) redirect("/login");

  const isAdmin = session.user.role === "ADMIN";

  return (
    <div className="md:flex">
      <Sidebar isAdmin={isAdmin} />

      <div className="min-w-0 flex-1">
        <header className="flex items-center justify-between gap-3 border-b border-slate-200 bg-white px-4 py-3 md:px-8">
          <div className="flex items-center gap-2 text-sm">
            <span className="font-medium text-slate-700">
              {session.user.name ?? session.user.email}
            </span>
            <Badge tom={isAdmin ? "azul" : "neutro"}>
              {isAdmin ? "Advogado" : "Cliente"}
            </Badge>
          </div>
          <form action={sair}>
            <button
              type="submit"
              className="flex items-center gap-1.5 rounded-lg px-2.5 py-1.5 text-sm font-medium text-slate-600 transition hover:bg-slate-100"
            >
              <LogOut className="h-4 w-4" />
              <span className="hidden sm:inline">Sair</span>
            </button>
          </form>
        </header>

        <main className="mx-auto max-w-7xl p-4 md:p-8">{children}</main>
      </div>
    </div>
  );
}
