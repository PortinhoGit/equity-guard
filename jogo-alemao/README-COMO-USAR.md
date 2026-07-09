# Wortsuche 🇩🇪 — Caça-Palavras de Alemão (Profª Catarina Portinho)

Jogo de caça-palavras em **alemão** com **tempo cronometrado** — feito de propósito
com pouco tempo por rodada para o aluno **pensar rápido em vez de consultar ChatGPT,
Google ou tradutor**. O aluno se cadastra (nome + e-mail), joga, ganha/perde pontos
por acerto e velocidade, e entra no ranking da turma.

É **um arquivo só** (`index.html`), sem servidor, sem instalação. Abre em qualquer
navegador (computador ou celular).

---

## 📁 Arquivos

| Arquivo | O que é |
|---|---|
| `index.html` | O jogo inteiro (design, lógica, palavras). |
| `catarina.jpg` | Foto da professora (avatar do cabeçalho). Troque quando quiser. |
| `catarina-solo.jpg` | Foto solo em alta, sobrando para usar em outra página se precisar. |
| `README-COMO-USAR.md` | Este guia. |

---

## 🚀 Como colocar no ar — o que eu recomendo

**Recomendação: Hostinger (upload direto).** É o caminho mais simples para um
subdomínio do `portinho.me`, sem depender de configuração de DNS extra.

### Opção A — Hostinger (recomendado, ~5 min)
1. No **hPanel** da Hostinger: **Domínios → Subdomínios** → crie, por ex., `alemao.portinho.me`.
2. Vá em **Gerenciador de Arquivos** e entre na pasta do subdomínio
   (algo como `public_html/alemao`).
3. Faça **upload** de `index.html` e `catarina.jpg` para dentro dessa pasta.
4. Pronto: acesse `https://alemao.portinho.me`.

> Por que Hostinger e não GitHub Pages? Você já tem a hospedagem e o domínio lá,
> então o subdomínio + SSL saem “de graça” e sem mexer em DNS. O GitHub Pages
> também funciona, mas exige apontar um registro CNAME do domínio para o GitHub.

### Opção B — GitHub Pages (bom se quiser versionar/editar pelo GitHub)
1. Este projeto já está no repositório, na pasta `jogo-alemao/`.
2. No repositório: **Settings → Pages** → Source: branch `main` (ou a de deploy) e
   pasta `/jogo-alemao` (ou mova os arquivos para a raiz de um repo próprio).
3. Para usar `alemao.portinho.me`: em **Settings → Pages → Custom domain** coloque
   `alemao.portinho.me` e crie um **CNAME** no DNS apontando para
   `SEU-USUARIO.github.io`.

Ambas funcionam. Para **rapidez agora**, use a **Hostinger**.

---

## 🖼️ Trocar a foto da professora

Basta substituir o arquivo `catarina.jpg` por outra foto (de preferência quadrada).
Se o arquivo não existir, o jogo mostra automaticamente um avatar com as iniciais.
Você também pode apontar para outro nome/URL no topo do `index.html`:

```js
FOTO: "catarina.jpg",   // ou "https://.../foto.png"
```

---

## ⚙️ Ajustar o jogo (tudo no topo do `index.html`)

No bloco `CONFIG` você controla, sem saber programar:

```js
SEGUNDOS_POR_RODADA: 75,    // ⏱️ tempo curto de propósito (anti-consulta)
TOTAL_RODADAS: 4,           // quantos temas por partida
TAMANHO_GRID: 12,           // tamanho da grade (12x12)
PONTOS_POR_PALAVRA: 100,    // base por palavra achada
BONUS_VELOCIDADE: 5,        // +pontos por segundo restante ao achar
PENALIDADE_ERRO: 40,        // desconto por seleção errada (evita chute)
BONUS_RODADA_COMPLETA: 150  // bônus por achar todas da rodada
```

Quer o tempo **ainda mais apertado** (mais difícil consultar IA)? Baixe
`SEGUNDOS_POR_RODADA` para `45` ou `60`.

---

## ✍️ Editar / adicionar palavras

Logo abaixo do `CONFIG`, na lista `TEMAS`. Cada tema é assim:

```js
{ tema:"Farben — Cores", dica:"As cores em alemão",
  palavras:[["ROT","vermelho"],["BLAU","azul"],["GELB","amarelo"]] },
```

- Use **MAIÚSCULAS**.
- `Ä Ö Ü ß` contam como **uma letra** (funciona normalmente).
- Cada palavra é um par `["ALEMÃO","tradução em português"]`.
- Pode criar quantos temas quiser — a cada partida o jogo sorteia `TOTAL_RODADAS`.

---

## 📊 Coletar os cadastros e pontuações

### Padrão (já funciona): ranking no navegador + CSV
- O ranking aparece na tela de fim de jogo.
- Botão **“Baixar CSV”** exporta nome, e-mail, pontos e data.
- ⚠️ Esses dados ficam **no navegador do aluno**. Bom para uma turma em sala,
  no mesmo computador/projetor. Para centralizar tudo, use o Google Sheets abaixo.

### Recomendado: enviar tudo para uma planilha (Google Sheets, grátis)
Assim **cada partida de cada aluno** cai automaticamente numa planilha sua.

1. Crie uma planilha nova em [sheets.google.com](https://sheets.google.com).
2. Menu **Extensões → Apps Script**. Apague o código e cole:

```js
function doPost(e) {
  var sheet = SpreadsheetApp.getActiveSpreadsheet().getSheets()[0];
  var d = JSON.parse(e.postData.contents);
  sheet.appendRow([new Date(), d.name, d.email, d.nota, d.score, d.date]);
  return ContentService.createTextOutput("ok");
}
```

3. Clique em **Implantar → Nova implantação → Tipo: App da Web**.
   - “Executar como”: **Eu**
   - “Quem tem acesso”: **Qualquer pessoa**
   - Clique **Implantar** e **copie a URL** gerada (termina em `/exec`).
4. No topo do `index.html`, cole essa URL:

```js
SHEETS_URL: "https://script.google.com/macros/s/AKfyc.../exec",
```

5. Pronto. A cada partida, uma nova linha aparece na sua planilha com
   data, nome, e-mail e pontuação. (O ranking na tela continua funcionando também.)

---

## 🎮 Como o aluno joga
1. Digita nome e e-mail e clica **Começar**.
2. Aparece a grade e a lista de palavras (com tradução).
3. **Arrasta** o dedo/mouse ligando as letras da palavra (em qualquer direção,
   inclusive diagonal e de trás pra frente).
4. Acertou → ganha pontos + bônus de velocidade. Errou → perde pontos.
5. O relógio corre; ao zerar, passa para o próximo tema.
6. No fim: pontuação, medalha e ranking da turma.

Bom jogo! 💜 *Viel Erfolg!*
