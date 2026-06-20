import { Construction } from "lucide-react";
import { PageHeader, EmptyState } from "@/components/ui";

// Placeholder das seções até a importação dos dados (Fase 2).
export function SecaoPlaceholder({
  titulo,
  descricao,
  conteudo,
}: {
  titulo: string;
  descricao: string;
  conteudo: string;
}) {
  return (
    <div>
      <PageHeader titulo={titulo} descricao={descricao} />
      <EmptyState
        icone={<Construction className="h-8 w-8" />}
        titulo="Seção pronta — aguardando importação dos dados"
        descricao={conteudo}
      />
    </div>
  );
}
