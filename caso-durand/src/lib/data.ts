import { prisma } from "./prisma";
import { diasAte } from "./format";

// Converte Decimal | null do Prisma para number.
function num(v: unknown): number {
  if (v === null || v === undefined) return 0;
  return Number(v);
}

export type Dashboard = {
  ok: boolean; // banco acessível com dados
  passivoTotal: number;
  passivoPorEmpresa: { empresa: string; total: number }[];
  contingencias: {
    valorEmRisco: number;
    porRisco: { PROVAVEL: number; POSSIVEL: number; REMOTO: number };
    total: number;
  };
  dueDiligence: { feitos: number; total: number; pct: number };
  cronograma: { concluidas: number; total: number; pct: number };
  certidoes: { vencidas: number; aVencer30: number; total: number };
  clausulas: { aRedigir: number; emRevisao: number; prontas: number; total: number };
};

const VAZIO: Dashboard = {
  ok: false,
  passivoTotal: 0,
  passivoPorEmpresa: [],
  contingencias: {
    valorEmRisco: 0,
    porRisco: { PROVAVEL: 0, POSSIVEL: 0, REMOTO: 0 },
    total: 0,
  },
  dueDiligence: { feitos: 0, total: 0, pct: 0 },
  cronograma: { concluidas: 0, total: 0, pct: 0 },
  certidoes: { vencidas: 0, aVencer30: 0, total: 0 },
  clausulas: { aRedigir: 0, emRevisao: 0, prontas: 0, total: 0 },
};

export async function getDashboard(): Promise<Dashboard> {
  try {
    const [
      resumos,
      contingencias,
      checklist,
      tarefas,
      certidoes,
      clausulas,
    ] = await Promise.all([
      prisma.passivoResumo.findMany({ include: { empresa: true } }),
      prisma.contingencia.findMany(),
      prisma.checklistItem.findMany(),
      prisma.tarefa.findMany(),
      prisma.certidao.findMany(),
      prisma.clausula.findMany(),
    ]);

    const passivoPorEmpresa = resumos.map((r) => ({
      empresa: r.empresa.nome,
      total: num(r.total ?? num(r.emprestimos) + num(r.dividasFiscais)),
    }));
    const passivoTotal = passivoPorEmpresa.reduce((s, e) => s + e.total, 0);

    const porRisco = { PROVAVEL: 0, POSSIVEL: 0, REMOTO: 0 };
    let valorEmRisco = 0;
    for (const c of contingencias) {
      porRisco[c.risco] += 1;
      valorEmRisco += num(c.valorEmRisco);
    }

    const ddFeitos = checklist.filter((c) => c.status === "TEMOS").length;
    const cronConcluidas = tarefas.filter(
      (t) => t.status === "CONCLUIDA",
    ).length;

    let vencidas = 0;
    let aVencer30 = 0;
    for (const cert of certidoes) {
      const d = diasAte(cert.validade);
      if (d === null) continue;
      if (d < 0) vencidas += 1;
      else if (d <= 30) aVencer30 += 1;
    }

    const cl = { aRedigir: 0, emRevisao: 0, prontas: 0 };
    for (const c of clausulas) {
      if (c.status === "A_REDIGIR") cl.aRedigir += 1;
      else if (c.status === "EM_REVISAO") cl.emRevisao += 1;
      else cl.prontas += 1;
    }

    const totalRegistros =
      resumos.length +
      contingencias.length +
      checklist.length +
      tarefas.length +
      certidoes.length +
      clausulas.length;

    return {
      ok: totalRegistros > 0,
      passivoTotal,
      passivoPorEmpresa,
      contingencias: {
        valorEmRisco,
        porRisco,
        total: contingencias.length,
      },
      dueDiligence: {
        feitos: ddFeitos,
        total: checklist.length,
        pct: checklist.length ? Math.round((ddFeitos / checklist.length) * 100) : 0,
      },
      cronograma: {
        concluidas: cronConcluidas,
        total: tarefas.length,
        pct: tarefas.length
          ? Math.round((cronConcluidas / tarefas.length) * 100)
          : 0,
      },
      certidoes: {
        vencidas,
        aVencer30,
        total: certidoes.length,
      },
      clausulas: { ...cl, total: clausulas.length },
    };
  } catch {
    // Banco ainda não migrado/conectado — UI mostra estado vazio.
    return VAZIO;
  }
}
