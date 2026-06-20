import { SecaoPlaceholder } from "@/components/SecaoPlaceholder";

export default function Page() {
  return (
    <SecaoPlaceholder
      titulo="Contingências"
      descricao="Processos judiciais, valor em risco e nível de risco."
      conteudo="Processos com classe, foro, valor da causa, risco (provável / possível / remoto) e recomendação. Será populado a partir da aba CONT."
    />
  );
}
