"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";
import {
  Home,
  CalendarRange,
  FileText,
  CheckSquare,
  ShieldCheck,
  AlertTriangle,
  Landmark,
  Users,
  Boxes,
  Download,
  ScrollText,
  Menu,
  X,
} from "lucide-react";
import { SECOES, SECOES_ADMIN } from "@/lib/constants";

const ICONES: Record<string, React.ComponentType<{ className?: string }>> = {
  home: Home,
  calendar: CalendarRange,
  file: FileText,
  check: CheckSquare,
  shield: ShieldCheck,
  alert: AlertTriangle,
  bank: Landmark,
  users: Users,
  box: Boxes,
  download: Download,
  log: ScrollText,
};

export function Sidebar({ isAdmin }: { isAdmin: boolean }) {
  const pathname = usePathname();
  const [aberto, setAberto] = useState(false);

  const itens = [...SECOES, ...(isAdmin ? SECOES_ADMIN : [])];

  const link = (href: string, label: string, icon: string) => {
    const Icone = ICONES[icon] ?? Home;
    const ativo = href === "/" ? pathname === "/" : pathname.startsWith(href);
    return (
      <Link
        key={href}
        href={href}
        onClick={() => setAberto(false)}
        className={`flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition ${
          ativo
            ? "bg-slate-900 text-white"
            : "text-slate-600 hover:bg-slate-100"
        }`}
      >
        <Icone className="h-4 w-4 shrink-0" />
        {label}
      </Link>
    );
  };

  return (
    <>
      {/* Barra superior mobile */}
      <div className="flex items-center justify-between border-b border-slate-200 bg-white px-4 py-3 md:hidden">
        <span className="font-semibold text-slate-900">Caso Durand</span>
        <button
          onClick={() => setAberto((v) => !v)}
          aria-label="Menu"
          className="rounded-lg p-1.5 text-slate-600 hover:bg-slate-100"
        >
          {aberto ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
        </button>
      </div>

      <nav
        className={`${
          aberto ? "block" : "hidden"
        } border-b border-slate-200 bg-white p-3 md:block md:h-screen md:w-60 md:shrink-0 md:border-r md:border-b-0`}
      >
        <div className="mb-4 hidden px-3 pt-2 md:block">
          <p className="text-sm font-semibold text-slate-900">Caso Durand</p>
          <p className="text-xs text-slate-500">Painel do contrato de M&amp;A</p>
        </div>
        <div className="space-y-1">
          {itens.map((s) => link(s.href, s.label, s.icon))}
        </div>
      </nav>
    </>
  );
}
