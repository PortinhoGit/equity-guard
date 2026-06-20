import { Info } from "lucide-react";
import { getDashboard } from "@/lib/data";
import { formatBRL } from "@/lib/format";
import { Card, PageHeader, StatCard } from "@/components/ui";
import { PassivoChart } from "@/components/charts/PassivoChart";

export const dynamic = "force-dynamic";

export default async function HomePage() {
  const d = await getDashboard();

  return (
    <div>
      <PageHeader
        titulo="Visão executiva"
        descricao="Resumo do contrato de aquisição — Grupo Durand."
      />

      {!d.ok && (
        <div className="mb-6 flex items-start gap-2 rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800">
          <Info className="mt-0.5 h-4 w-4 shrink-0" />
          <span>
            Ainda não há dados no banco. Rode o script de importação da planilha
            (Fase 2) para popular os indicadores abaixo.
          </span>
        </div>
      )}

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard
          rotulo="Passivo total do grupo"
          valor={formatBRL(d.passivoTotal)}
          detalhe={`${d.passivoPorEmpresa.length} empresa(s)`}
        />
        <StatCard
          rotulo="Valor em risco (contingências)"
          valor={formatBRL(d.contingencias.valorEmRisco)}
          detalhe={`${d.contingencias.total} processo(s)`}
          tom="vermelho"
        />
        <StatCard
          rotulo="Avanço da due diligence"
          valor={`${d.dueDiligence.pct}%`}
          detalhe={`${d.dueDiligence.feitos}/${d.dueDiligence.total} itens`}
          tom="verde"
        />
        <StatCard
          rotulo="Avanço do cronograma"
          valor={`${d.cronograma.pct}%`}
          detalhe={`${d.cronograma.concluidas}/${d.cronograma.total} tarefas`}
          tom="azul"
        />
      </div>

      <div className="mt-4 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard
          rotulo="Certidões vencidas"
          valor={d.certidoes.vencidas}
          detalhe={`de ${d.certidoes.total} certidões`}
          tom={d.certidoes.vencidas > 0 ? "vermelho" : "verde"}
        />
        <StatCard
          rotulo="Certidões a vencer (30 dias)"
          valor={d.certidoes.aVencer30}
          tom={d.certidoes.aVencer30 > 0 ? "amarelo" : "verde"}
        />
        <StatCard
          rotulo="Cláusulas prontas"
          valor={`${d.clausulas.prontas}/${d.clausulas.total}`}
          detalhe={`${d.clausulas.aRedigir} a redigir`}
        />
        <StatCard
          rotulo="Processos por risco"
          valor={`${d.contingencias.porRisco.PROVAVEL} prováveis`}
          detalhe={`${d.contingencias.porRisco.POSSIVEL} possíveis · ${d.contingencias.porRisco.REMOTO} remotos`}
          tom="amarelo"
        />
      </div>

      <div className="mt-4 grid grid-cols-1 gap-4 lg:grid-cols-2">
        <Card>
          <h2 className="mb-3 text-sm font-semibold text-slate-700">
            Passivo por empresa
          </h2>
          <PassivoChart dados={d.passivoPorEmpresa} />
        </Card>
        <Card>
          <h2 className="mb-3 text-sm font-semibold text-slate-700">
            Caminho crítico
          </h2>
          <ul className="space-y-2 text-sm text-slate-600">
            <li className="flex items-center gap-2">
              <span className="h-2 w-2 rounded-full bg-amber-500" />
              Laranja / Plast Log — definição de estrutura
            </li>
            <li className="flex items-center gap-2">
              <span className="h-2 w-2 rounded-full bg-amber-500" />
              Banco do Brasil — avais cruzados e liberação
            </li>
            <li className="flex items-center gap-2">
              <span className="h-2 w-2 rounded-full bg-amber-500" />
              Escrow — retenção de parte do preço
            </li>
            <li className="mt-2 text-xs text-slate-400">
              Os prazos do caminho crítico serão ligados ao cronograma na Fase 4.
            </li>
          </ul>
        </Card>
      </div>
    </div>
  );
}
