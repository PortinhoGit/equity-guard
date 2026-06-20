import { SecaoPlaceholder } from "@/components/SecaoPlaceholder";

export default function Page() {
  return (
    <SecaoPlaceholder
      titulo="Controle de Certidões"
      descricao="~70 certidões com titular, órgão, situação, emissão e validade."
      conteudo="Tabela com alerta de vencimento (semáforo). Será populada a partir da aba CERT da planilha-mãe."
    />
  );
}
