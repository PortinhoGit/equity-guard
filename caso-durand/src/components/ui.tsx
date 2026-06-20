import type { ReactNode } from "react";

export function Card({
  children,
  className = "",
}: {
  children: ReactNode;
  className?: string;
}) {
  return (
    <div
      className={`rounded-xl border border-slate-200 bg-white p-5 shadow-sm ${className}`}
    >
      {children}
    </div>
  );
}

export function PageHeader({
  titulo,
  descricao,
  acao,
}: {
  titulo: string;
  descricao?: string;
  acao?: ReactNode;
}) {
  return (
    <div className="mb-6 flex flex-wrap items-end justify-between gap-3">
      <div>
        <h1 className="text-xl font-semibold text-slate-900">{titulo}</h1>
        {descricao && (
          <p className="mt-1 text-sm text-slate-500">{descricao}</p>
        )}
      </div>
      {acao}
    </div>
  );
}

export function StatCard({
  rotulo,
  valor,
  detalhe,
  tom = "neutro",
}: {
  rotulo: string;
  valor: ReactNode;
  detalhe?: ReactNode;
  tom?: "neutro" | "verde" | "amarelo" | "vermelho" | "azul";
}) {
  const tons: Record<string, string> = {
    neutro: "text-slate-900",
    verde: "text-emerald-600",
    amarelo: "text-amber-600",
    vermelho: "text-red-600",
    azul: "text-blue-600",
  };
  return (
    <Card>
      <p className="text-xs font-medium uppercase tracking-wide text-slate-500">
        {rotulo}
      </p>
      <p className={`mt-2 text-2xl font-semibold ${tons[tom]}`}>{valor}</p>
      {detalhe && <p className="mt-1 text-xs text-slate-500">{detalhe}</p>}
    </Card>
  );
}

export function Badge({
  children,
  tom = "neutro",
}: {
  children: ReactNode;
  tom?: "neutro" | "verde" | "amarelo" | "vermelho" | "azul";
}) {
  const tons: Record<string, string> = {
    neutro: "bg-slate-100 text-slate-700",
    verde: "bg-emerald-100 text-emerald-700",
    amarelo: "bg-amber-100 text-amber-700",
    vermelho: "bg-red-100 text-red-700",
    azul: "bg-blue-100 text-blue-700",
  };
  return (
    <span
      className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${tons[tom]}`}
    >
      {children}
    </span>
  );
}

export function EmptyState({
  titulo,
  descricao,
  icone,
}: {
  titulo: string;
  descricao?: string;
  icone?: ReactNode;
}) {
  return (
    <Card className="flex flex-col items-center justify-center py-12 text-center">
      {icone && <div className="mb-3 text-slate-400">{icone}</div>}
      <p className="font-medium text-slate-700">{titulo}</p>
      {descricao && (
        <p className="mt-1 max-w-md text-sm text-slate-500">{descricao}</p>
      )}
    </Card>
  );
}
