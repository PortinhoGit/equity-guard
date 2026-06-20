import { SecaoPlaceholder } from "@/components/SecaoPlaceholder";

export default function Page() {
  return (
    <SecaoPlaceholder
      titulo="Passivos"
      descricao="Empréstimos, dívidas fiscais, garantias/avais e consolidado."
      conteudo="Consolidação de passivos por empresa. Será populada a partir das abas PASS (Resumo, Empréstimos, Dívidas Fiscais, Garantias e Consolidado)."
    />
  );
}
