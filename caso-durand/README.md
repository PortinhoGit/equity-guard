# Painel do Contrato — Caso Durand

Site privado para gestão do contrato de M&A (aquisição da participação no Grupo
Durand). Ferramenta interna e **sigilosa**, de uso restrito a duas pessoas
(advogado e cliente). Materializa, em formato de dashboard editável, a
planilha-mãe `00_PLANILHA_MAE_Grupo_Durand_v7.xlsx`.

> ⚠️ **Sigilo e LGPD.** Os dados contêm CPF, valores, dívidas e processos.
> O repositório deve ser **privado**. A planilha (`.xlsx`) e o arquivo `.env`
> **nunca** podem ser commitados (já estão no `.gitignore`).

---

## Tecnologias

- **Next.js 16** (App Router) + **TypeScript** + **Tailwind CSS**
- **Supabase** (PostgreSQL gerenciado, região São Paulo) + **Prisma** (ORM)
- **Auth.js (NextAuth v5)** — login por e-mail/senha, sem cadastro público
- **argon2** para hash de senha · **Recharts** (gráficos) · **SheetJS** (Excel)
- Deploy na **Vercel**

---

## 1. Rodar localmente (no seu computador)

Pré-requisitos: **Node.js 20+** instalado.

```bash
# 1. Instalar as dependências
npm install

# 2. Criar o arquivo de variáveis de ambiente
cp .env.example .env
#    → edite o .env e preencha (ver seção 2)

# 3. Criar as tabelas no banco
npm run db:push

# 4. Criar os dois usuários (lê e-mails/senhas do .env)
npm run db:seed

# 5. Importar a planilha (coloque o .xlsx na pasta do projeto antes)
npm run db:import

# 6. Subir o site em modo desenvolvimento
npm run dev
#    → abra http://localhost:3000
```

---

## 2. Configurar o `.env`

Copie `.env.example` para `.env` e preencha:

| Variável | O que é |
|---|---|
| `DATABASE_URL` | String de conexão do Supabase (porta **6543**, o "pooler"). |
| `DIRECT_URL` | String de conexão direta do Supabase (porta **5432**). Usada em migrações/seed. |
| `AUTH_SECRET` | Segredo para assinar as sessões. Gere com `openssl rand -base64 32`. |
| `AUTH_URL` | Endereço do site (`http://localhost:3000` local; `https://durand.portinho.me` em produção). |
| `ADMIN_EMAIL` / `ADMIN_NOME` / `ADMIN_SENHA` | Dados do **advogado** (perfil admin). |
| `CLIENTE_EMAIL` / `CLIENTE_NOME` / `CLIENTE_SENHA` | Dados do **Beto** (perfil cliente). |
| `IMPORT_FILE` | Caminho da planilha-mãe para importação local. |

As **senhas** são obrigatoriamente fortes: mínimo de 12 caracteres, com
maiúscula, minúscula, número e símbolo.

### Onde pego as strings do Supabase?

1. Crie uma conta em [supabase.com](https://supabase.com) e um **novo projeto**.
2. **Importante:** na criação, escolha a região **São Paulo (sa-east-1)**.
3. Em **Project Settings → Database → Connection string**, copie:
   - a string do **Connection pooling** (porta 6543) → `DATABASE_URL`
   - a string da **Direct connection** (porta 5432) → `DIRECT_URL`
4. Troque `[YOUR-PASSWORD]` pela senha do banco que você definiu.

---

## 3. Importar a planilha (xlsx → banco)

A planilha é importada **uma vez** para o banco; depois disso, o **banco é a
fonte única da verdade** (todas as edições no site ficam no banco).

```bash
# Ver as abas e colunas detectadas (não grava nada) — útil para conferência
npm run db:import -- --inspect

# Importar de fato
npm run db:import
```

Coloque o arquivo `00_PLANILHA_MAE_Grupo_Durand_v7.xlsx` na pasta do projeto
(ou aponte o caminho em `IMPORT_FILE`). Ele **não** é versionado pelo Git.

> O mapeamento detalhado das 20 abas é calibrado na Fase 2 com o arquivo real
> (rode `--inspect` para conferir os nomes de abas/colunas).

---

## 4. Criar e trocar as senhas dos dois usuários

Os usuários são criados pelo **seed**, que lê do `.env`. Não há cadastro aberto.

**Criar/atualizar:** edite `ADMIN_SENHA` / `CLIENTE_SENHA` no `.env` e rode:

```bash
npm run db:seed
```

O seed é idempotente: rodar de novo **atualiza** os usuários existentes (mesmo
e-mail) com a nova senha. Para trocar uma senha, basta mudar no `.env` e rodar
`npm run db:seed` novamente.

---

## 5. Publicar na internet (deploy) — passo a passo para leigo

O site roda na **Vercel** (hospeda a aplicação), com o **banco no Supabase**, e
fica acessível em **`durand.portinho.me`** (subdomínio do seu domínio na
Hostinger). A Hostinger entra **só com o DNS** — não hospeda o site.

### Passo 1 — Subir o código para um repositório privado no GitHub

1. No GitHub, crie um **repositório privado** (ex.: `caso-durand`).
2. Envie este projeto para ele (a planilha e o `.env` ficam de fora).

### Passo 2 — Criar o projeto na Vercel

1. Acesse [vercel.com](https://vercel.com) e faça login com o GitHub.
2. **Add New → Project** e selecione o repositório `caso-durand`.
3. A Vercel detecta Next.js automaticamente. **Não** clique em Deploy ainda —
   primeiro configure as variáveis de ambiente (Passo 3).

### Passo 3 — Variáveis de ambiente na Vercel

Em **Settings → Environment Variables**, adicione (valores de produção):

- `DATABASE_URL` (pooler, 6543)
- `DIRECT_URL` (direto, 5432)
- `AUTH_SECRET` (gere um novo, diferente do local)
- `AUTH_URL` = `https://durand.portinho.me`

Depois clique em **Deploy**.

### Passo 4 — Adicionar o domínio `durand.portinho.me` na Vercel

1. No projeto, vá em **Settings → Domains**.
2. Digite `durand.portinho.me` e clique **Add**.
3. A Vercel mostrará o **alvo do CNAME** (normalmente `cname.vercel-dns.com`).
   **Anote o alvo exato exibido.**

### Passo 5 — Criar o CNAME no DNS da Hostinger

1. Entre no **hPanel** da Hostinger → **Domínios** → **Zona DNS / DNS Zone Editor**
   do domínio `portinho.me`.
2. **Adicionar registro:**
   - **Tipo:** `CNAME`
   - **Nome / Host:** `durand`
   - **Aponta para / Target:** o alvo que a Vercel mostrou (ex.: `cname.vercel-dns.com`)
   - **TTL:** padrão
3. Salve e **aguarde a propagação** (de minutos a algumas horas). A Vercel
   marca o domínio como válido e emite o certificado HTTPS automaticamente.

### Passo 6 — Preparar o banco em produção (rodar uma vez)

No seu computador, com o `.env` apontando para o banco **de produção** (Supabase):

```bash
npm run db:push     # cria as tabelas
npm run db:seed     # cria os dois usuários
npm run db:import   # importa a planilha
```

Pronto: acesse `https://durand.portinho.me` e faça login.

> A partir daí, cada `git push` no repositório dispara um **deploy automático**
> na Vercel.

---

## Segurança (resumo)

- Todas as rotas exigem login (proxy de autenticação). Nada é público.
- Sem cadastro aberto e sem "esqueci a senha" público — só os dois usuários.
- Senhas com hash **argon2**; política de senha forte no seed.
- Sessão curta (8h) com re-login; cookies `httpOnly`/`secure`.
- `robots.txt` e cabeçalhos `noindex` impedem indexação por buscadores.
- Cabeçalhos de segurança (HSTS, X-Frame-Options, etc.) e HTTPS na Vercel.
- Dados em repouso no Postgres (Supabase **São Paulo**); em trânsito via TLS.
- `.env` e `.xlsx` fora do Git. **Mantenha o repositório privado.**

---

## Comandos úteis

| Comando | O que faz |
|---|---|
| `npm run dev` | Sobe o site em desenvolvimento (localhost:3000). |
| `npm run build` | Gera a build de produção. |
| `npm run db:push` | Cria/atualiza as tabelas no banco. |
| `npm run db:seed` | Cria/atualiza os dois usuários (lê o `.env`). |
| `npm run db:import` | Importa a planilha para o banco. |
| `npm run db:import -- --inspect` | Lista abas/colunas da planilha sem gravar. |

---

## Roadmap (fases)

- **Fase 0 + 1 (concluída):** fundação, autenticação, schema do banco, seed dos
  usuários, segurança (noindex/headers), shell de navegação e home com KPIs.
- **Fase 2:** importação calibrada da planilha + tabelas de leitura por seção.
- **Fase 3:** edição inline + trilha de auditoria + comentários por item.
- **Fase 4:** alertas (certidões/cronograma) + exportação Excel e PDF.
- **Fase 5 (opcional):** anexos de documentos (bucket privado no Supabase).
