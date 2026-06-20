/**
 * Importador da planilha-mãe (xlsx → banco).
 *
 * Roda UMA vez localmente para popular o banco. Depois disso, o banco é a
 * fonte única da verdade. A planilha NÃO vai para o Git.
 *
 * Uso:
 *   IMPORT_FILE=./00_PLANILHA_MAE_Grupo_Durand_v7.xlsx npm run db:import
 *
 * Modos:
 *   --inspect   apenas lista as abas e as colunas (cabeçalhos) detectadas,
 *               sem gravar nada. Use para calibrar o mapeamento (Fase 2).
 *
 * NOTA (Fase 2): o mapeamento exato coluna→campo de cada aba será finalizado
 * ao rodar `--inspect` no arquivo real. Os parsers abaixo (R$, data, status)
 * já estão prontos; as empresas já são semeadas.
 */
import * as fs from "node:fs";
import * as XLSX from "xlsx";
import { PrismaClient } from "@prisma/client";
import { EMPRESAS } from "../src/lib/constants";

const prisma = new PrismaClient();

const ARQUIVO =
  process.env.IMPORT_FILE || "./00_PLANILHA_MAE_Grupo_Durand_v7.xlsx";
const INSPECT = process.argv.includes("--inspect");

// ───────────── Parsers de valores da planilha ─────────────

/** "R$ 1.234.567,89" | "1.234,56" | número → number | null */
export function parseBRL(v: unknown): number | null {
  if (v === null || v === undefined || v === "") return null;
  if (typeof v === "number") return v;
  const s = String(v)
    .replace(/[R$\s]/g, "")
    .replace(/\./g, "")
    .replace(",", ".");
  const n = Number(s);
  return Number.isNaN(n) ? null : n;
}

/** Data Excel (serial) ou string dd/mm/aaaa → Date | null */
export function parseData(v: unknown): Date | null {
  if (v === null || v === undefined || v === "") return null;
  if (v instanceof Date) return v;
  if (typeof v === "number") {
    const d = XLSX.SSF ? XLSX.SSF.parse_date_code(v) : null;
    if (d) return new Date(Date.UTC(d.y, d.m - 1, d.d));
  }
  const s = String(v).trim();
  const br = s.match(/^(\d{1,2})\/(\d{1,2})\/(\d{2,4})$/);
  if (br) {
    const [, dd, mm, yy] = br;
    const ano = yy.length === 2 ? 2000 + Number(yy) : Number(yy);
    return new Date(Date.UTC(ano, Number(mm) - 1, Number(dd)));
  }
  const d = new Date(s);
  return Number.isNaN(d.getTime()) ? null : d;
}

/** Normaliza status de checklist a partir de texto/emoji */
export function parseStatusChecklist(
  v: unknown,
): "TEMOS" | "PARCIAL" | "FALTA" {
  const s = String(v ?? "").toLowerCase();
  if (s.includes("✔") || s.includes("temos") || s.includes("ok")) return "TEMOS";
  if (s.includes("◐") || s.includes("parcial")) return "PARCIAL";
  return "FALTA";
}

// ───────────── Helpers ─────────────

function sheetToRows(wb: XLSX.WorkBook, nome: string): Record<string, unknown>[] {
  const ws = wb.Sheets[nome];
  if (!ws) return [];
  return XLSX.utils.sheet_to_json(ws, { defval: null, raw: true });
}

async function seedEmpresas() {
  for (const nome of EMPRESAS) {
    await prisma.empresa.upsert({
      where: { nome },
      update: {},
      create: { nome },
    });
  }
  console.log(`✓ ${EMPRESAS.length} empresas semeadas.`);
}

// ───────────── Execução ─────────────

async function main() {
  if (!fs.existsSync(ARQUIVO)) {
    console.error(
      `✗ Planilha não encontrada: ${ARQUIVO}\n` +
        `  Coloque o arquivo na pasta do projeto (ele NÃO é versionado) ou defina IMPORT_FILE.`,
    );
    process.exit(1);
  }

  const wb = XLSX.readFile(ARQUIVO, { cellDates: true });
  console.log(`Abas encontradas (${wb.SheetNames.length}):`);

  for (const nome of wb.SheetNames) {
    const rows = sheetToRows(wb, nome);
    const colunas = rows.length ? Object.keys(rows[0]) : [];
    console.log(`\n• ${nome}  (${rows.length} linhas)`);
    if (INSPECT) console.log(`    colunas: ${colunas.join(" | ")}`);
  }

  if (INSPECT) {
    console.log(
      "\nModo inspeção concluído. Nenhum dado gravado.\n" +
        "Use estes nomes de abas/colunas para finalizar o mapeamento na Fase 2.",
    );
    await prisma.$disconnect();
    return;
  }

  // Semeia entidades-base. O mapeamento detalhado das 20 abas → tabelas é
  // ativado na Fase 2, após calibrar com `--inspect` no arquivo real.
  await seedEmpresas();

  console.log(
    "\n⚠ Importação detalhada das abas ainda não calibrada (Fase 2).\n" +
      "  Rode `npm run db:import -- --inspect` para ver as colunas reais.",
  );

  await prisma.$disconnect();
}

main().catch(async (e) => {
  console.error(e);
  await prisma.$disconnect();
  process.exit(1);
});
