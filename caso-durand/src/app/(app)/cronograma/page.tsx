import { SecaoPlaceholder } from "@/components/SecaoPlaceholder";

export default function Page() {
  return (
    <SecaoPlaceholder
      titulo="Cronograma — 3 meses"
      descricao="Plano de trabalho por semana, fases Antes / Durante / Depois."
      conteudo="Tabela de tarefas com responsável, fase, semana e status (editável). Será populada a partir da aba CRON da planilha-mãe."
    />
  );
}
