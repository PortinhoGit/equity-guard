"""
legal_pages.py — Equity Guard
Paginas legais acessadas via query param (?page=privacidade ou ?page=termos).

Texto base redigido em linguagem clara (LGPD Art. 9 exige transparencia).
Para producao com grande volume de usuarios, recomenda-se revisao juridica.
"""

from datetime import date
import streamlit as st


_CONTROLLER_NAME = "Equity Guard — Projeto operado por José Portinho Júnior"
_CONTACT_EMAIL = "portinho@icloud.com"
_LAST_UPDATE = date(2026, 4, 20)  # Atualizar quando textos mudarem
_APP_URL = "https://equityguard.streamlit.app"


def _render_back_button(suffix: str = "top") -> None:
    if st.button("← Voltar ao app", key=f"legal_back_{suffix}"):
        st.query_params.clear()
        st.rerun()


def _render_header(title: str) -> None:
    st.markdown(
        "<h1 style='font-size:1.7rem;font-weight:900;letter-spacing:-.5px;margin-bottom:4px;'>"
        "<span style='color:#d4af37;'>EQUITY</span>"
        "<span style='color:#e6edf3;'> GUARD</span>"
        "</h1>",
        unsafe_allow_html=True,
    )
    st.markdown(
        f"<h2 style='font-size:1.35rem;color:#e6edf3;margin-top:1rem;'>{title}</h2>"
        f"<div style='font-size:.78rem;color:#8b949e;margin-bottom:1rem;'>"
        f"Última atualização: {_LAST_UPDATE.strftime('%d/%m/%Y')}</div>",
        unsafe_allow_html=True,
    )


def render_privacy_page() -> None:
    _render_back_button("priv_top")
    _render_header("Política de Privacidade")

    st.markdown(
        f"""
Esta Política de Privacidade descreve como o **Equity Guard** ({_APP_URL})
coleta, usa, armazena e protege seus dados pessoais, em conformidade com a
**Lei Geral de Proteção de Dados (Lei nº 13.709/2018 — LGPD)**.

---

#### 1. Controlador dos dados

O controlador responsável pelo tratamento dos seus dados pessoais é:

**{_CONTROLLER_NAME}**
Contato para assuntos de privacidade: **{_CONTACT_EMAIL}**

---

#### 2. Quais dados coletamos

**Dados fornecidos por você:**
- Endereço de e-mail (quando você se cadastra)
- Mensagens enviadas pela caixa de feedback

**Dados coletados automaticamente:**
- Endereço IP (de forma anônima, via Google Analytics)
- Tipo de dispositivo, navegador e sistema operacional
- Páginas visitadas e tempo de sessão
- Tickers consultados (armazenados se você estiver logado)
- Data e hora do acesso

**Dados NÃO coletados:**
- CPF, RG ou qualquer documento de identificação oficial
- Senhas bancárias, números de conta ou cartão de crédito
- Dados de corretora ou carteira real de investimentos
- Dados sensíveis (origem racial, religião, orientação sexual, saúde, etc.)

---

#### 3. Para que usamos seus dados

- **E-mail:** identificar seu cadastro, enviar notificações relacionadas ao serviço
- **Histórico de tickers:** permitir que você acesse rapidamente suas ações favoritas
- **Dados de uso (analytics):** entender como o app é utilizado e priorizar melhorias
- **Feedback:** responder mensagens e corrigir problemas relatados

---

#### 4. Base legal (LGPD Art. 7º)

- **Consentimento:** para coleta de e-mail e uso de cookies de analytics
- **Legítimo interesse:** para análise de uso agregada e prevenção de abuso

---

#### 5. Compartilhamento de dados

Seus dados **não são vendidos nem compartilhados para fins comerciais**. Os únicos
terceiros com acesso a dados anonimizados são:

- **Google Analytics** (`G-BBKMK9TL6P`) — métricas de uso agregadas
- **Streamlit Inc.** — infraestrutura de hospedagem do app
- **Yahoo Finance** — fornecedor dos dados de mercado (não recebe seus dados pessoais)
- **Google** (via Gmail SMTP) — envio de e-mails de feedback aos mantenedores

Nenhum desses terceiros recebe seu e-mail, senha ou histórico de navegação
de forma direta.

---

#### 6. Armazenamento e segurança

- Dados de cadastro são armazenados em servidor gerenciado pelo Streamlit Cloud
- Conexões são protegidas por **HTTPS** (TLS)
- O código-fonte é aberto e pode ser auditado em
  [github.com/PortinhoGit/equity-guard](https://github.com/PortinhoGit/equity-guard)
- Nenhum dado sensível é armazenado (ver seção 2)

**Importante:** este é um app em **versão beta**. Para uso com grande volume de
dados sensíveis recomenda-se aguardar a versão de produção estável, que terá
criptografia adicional no banco de usuários.

---

#### 7. Seus direitos (LGPD Art. 18)

Você pode, a qualquer momento, solicitar:

- **Confirmação** da existência de tratamento dos seus dados
- **Acesso** aos dados que mantemos sobre você
- **Correção** de dados incompletos ou desatualizados
- **Anonimização ou eliminação** de dados desnecessários
- **Portabilidade** a outro serviço
- **Revogação do consentimento** e exclusão dos dados coletados com base nele
- **Informações** sobre compartilhamentos de dados realizados

Para exercer qualquer desses direitos, envie um e-mail para **{_CONTACT_EMAIL}**
com a solicitação. Responderemos em até **15 dias corridos**.

---

#### 8. Cookies e rastreamento

Usamos cookies e tecnologias similares para:

- Manter sua sessão ativa (cookie técnico essencial — não requer consentimento)
- Análise de uso agregada via Google Analytics (requer consentimento)

Você pode recusar cookies de analytics no banner exibido na primeira visita,
ou limpá-los a qualquer momento nas configurações do seu navegador.

---

#### 9. Retenção de dados

- **Dados de cadastro:** mantidos enquanto sua conta estiver ativa. Após
  solicitação de exclusão, removidos em até 15 dias.
- **Logs de uso:** retidos por até **12 meses** para análise de tendências,
  após o que são anonimizados ou eliminados.

---

#### 10. Alterações nesta política

Esta política pode ser atualizada periodicamente. Mudanças relevantes serão
comunicadas por aviso no próprio app. A data de última atualização é exibida
no topo desta página.

---

#### 11. Contato

Para dúvidas sobre privacidade, exercer direitos ou reportar incidentes:

**{_CONTACT_EMAIL}**
""",
        unsafe_allow_html=False,
    )
    st.divider()
    _render_back_button("priv_bot")


def render_terms_page() -> None:
    _render_back_button("terms_top")
    _render_header("Termos de Uso")

    st.markdown(
        f"""
Ao acessar e usar o **Equity Guard** ({_APP_URL}), você concorda com estes
Termos de Uso. Se não concordar, não utilize o serviço.

---

#### 1. Sobre o serviço

O Equity Guard é uma **ferramenta educacional de análise de ações** da B3 e de
mercados internacionais. Ele reúne:

- Cotações e dados fundamentalistas (fonte: Yahoo Finance)
- Indicadores técnicos (RSI, MMs, candles)
- Cálculo de Preço Teto pelo método Barsi
- Análise estruturada gerada automaticamente

**O Equity Guard NÃO é:**

- Consultoria financeira ou de investimentos
- Recomendação de compra, venda ou manutenção de qualquer ativo
- Plataforma de negociação — o app não executa ordens em corretora
- Garantia de retorno financeiro

---

#### 2. Natureza das informações — Disclaimer

Todos os dados, análises, projeções, sinais, indicadores técnicos e cálculos
(incluindo Preço Teto pelo método Barsi, RSI, Médias Móveis, Tendências,
Dividend Yield, Payout Ratio, ROE, P/L, P/VP e demais métricas) gerados pelo
Equity Guard têm **caráter exclusivamente informativo e educacional**.

**O Equity Guard NÃO constitui, sob hipótese alguma:**

- Recomendação de **compra, venda ou manutenção** de qualquer ativo financeiro
- Recomendação de **entrada ou saída** da bolsa de valores, de fundos ou de
  qualquer mercado
- Oferta, solicitação ou indução à aquisição de valores mobiliários
- Consultoria ou assessoria de investimentos individual ou personalizada
- Análise de perfil de investidor (suitability)
- Garantia, promessa ou expectativa de rentabilidade, lucro, proteção contra
  perdas ou qualquer resultado financeiro específico

**Fatos que o usuário deve considerar:**

- **Riscos de mercado são reais.** Investir em renda variável pode resultar em
  **perda parcial ou total** do capital aplicado. Não há retorno garantido.
- **Rentabilidade passada não representa garantia de rentabilidade futura.**
  Qualquer projeção é baseada em modelos matemáticos e premissas que podem
  não se concretizar.
- **Os dados podem conter erros, atrasos ou falhas.** As cotações são fornecidas
  por Yahoo Finance, B3 e outras fontes públicas, e podem apresentar
  divergências em relação ao preço real negociado na bolsa.
- **Indicadores técnicos (RSI, MMs, Golden/Death Cross) são ferramentas**
  estatísticas com limitações conhecidas. Não funcionam em todos os cenários
  e podem gerar sinais falsos.
- **O método do Preço Teto (Barsi)** assume premissas como dividend yield
  desejado e histórico de dividendos, que podem não se manter no futuro.
- **Tributos, taxas de corretagem e emolumentos** não são considerados nos
  cálculos de retorno e podem impactar significativamente o resultado final.
- **Responsabilidade fiscal** pelas operações realizadas é integralmente do
  usuário.

**Antes de qualquer decisão de investimento, consulte:**

- Um **Consultor de Valores Mobiliários** credenciado pela CVM (Comissão de
  Valores Mobiliários), conforme a Resolução CVM nº 19/2021
- Um **Analista de Valores Mobiliários** certificado pela APIMEC (Associação
  dos Analistas e Profissionais de Investimento do Mercado de Capitais)
- Seu **Assessor de Investimentos** (anteriormente conhecido como Agente
  Autônomo de Investimentos — AAI), credenciado junto à CVM e vinculado a uma
  corretora

O Equity Guard e seus mantenedores **não são credenciados pela CVM** para
prestação de serviços de consultoria, análise ou assessoria de investimentos.
Este app é uma ferramenta de apoio ao estudo individual do mercado.

**Decisões de investimento são de responsabilidade única, exclusiva e
intransferível do usuário.** Ao utilizar o Equity Guard, você declara estar
ciente de que opera por sua própria conta e risco, e isenta os mantenedores
do app de qualquer responsabilidade por ganhos, perdas ou prejuízos
decorrentes de suas decisões financeiras.

---

#### 3. Responsabilidades do usuário

Ao usar o Equity Guard, você concorda em:

- Fornecer informações verdadeiras ao se cadastrar
- Não utilizar o serviço para fins ilegais ou abusivos
- Não tentar sobrecarregar, invadir ou burlar sistemas do app
- Não usar o app para qualquer atividade fraudulenta
- Respeitar os direitos de propriedade intelectual

---

#### 4. Limitação de responsabilidade

O Equity Guard é disponibilizado **"no estado em que se encontra"**, sem
garantias de qualquer tipo. Os mantenedores **não se responsabilizam** por:

- Erros, atrasos ou interrupções nos dados de mercado
- Perdas financeiras decorrentes de decisões baseadas nas análises
- Indisponibilidade temporária do serviço
- Falhas em serviços de terceiros (Yahoo Finance, Streamlit Cloud, Google)

**Em nenhuma hipótese** os mantenedores serão responsáveis por danos diretos,
indiretos, incidentais, especiais ou consequenciais decorrentes do uso ou
incapacidade de uso do app.

---

#### 5. Propriedade intelectual

O código-fonte do Equity Guard é disponibilizado publicamente em
[github.com/PortinhoGit/equity-guard](https://github.com/PortinhoGit/equity-guard).

O nome "Equity Guard", o logo e a identidade visual são de titularidade do
controlador (ver Política de Privacidade).

Dados de cotação e indicadores pertencem aos seus respectivos fornecedores
(Yahoo Finance, B3, etc.).

---

#### 6. Modificações no serviço

O Equity Guard está em **versão beta**. Funcionalidades podem ser adicionadas,
modificadas ou removidas a qualquer momento, sem aviso prévio.

---

#### 7. Suspensão de acesso

Podemos suspender ou encerrar o acesso de qualquer usuário que violar estes
Termos, sem necessidade de aviso prévio ou indenização.

---

#### 8. Alterações nos Termos

Estes Termos podem ser atualizados periodicamente. Mudanças relevantes serão
comunicadas por aviso no próprio app. Ao continuar usando o serviço após
atualizações, você concorda com os novos Termos.

---

#### 9. Legislação aplicável

Estes Termos são regidos pelas **leis da República Federativa do Brasil**.
Eventuais disputas serão resolvidas no foro de eleição do controlador.

---

#### 10. Contato

Para dúvidas, sugestões ou reportes:

**{_CONTACT_EMAIL}**
""",
        unsafe_allow_html=False,
    )
    st.divider()
    _render_back_button("terms_bot")
