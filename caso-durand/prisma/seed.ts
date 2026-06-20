/**
 * Seed dos DOIS usuários (sem auto-cadastro).
 * Lê e-mails/nomes/senhas das variáveis de ambiente, valida senha forte,
 * gera hash argon2 e grava/atualiza no banco. Idempotente (upsert por e-mail).
 *
 * Uso:
 *   ADMIN_EMAIL=... ADMIN_NOME=... ADMIN_SENHA=... \
 *   CLIENTE_EMAIL=... CLIENTE_NOME=... CLIENTE_SENHA=... \
 *   npm run db:seed
 */
import { PrismaClient } from "@prisma/client";
import { hashPassword, validarSenhaForte } from "../src/lib/password";

const prisma = new PrismaClient();

function exigir(nome: string): string {
  const v = process.env[nome];
  if (!v || !v.trim()) {
    console.error(`✗ Variável de ambiente obrigatória ausente: ${nome}`);
    process.exit(1);
  }
  return v.trim();
}

async function upsertUsuario(
  email: string,
  nome: string,
  senha: string,
  role: "ADMIN" | "CLIENTE",
) {
  const erro = validarSenhaForte(senha);
  if (erro) {
    console.error(`✗ Senha inválida para ${email}: ${erro}`);
    process.exit(1);
  }
  const senhaHash = await hashPassword(senha);
  const u = await prisma.user.upsert({
    where: { email: email.toLowerCase() },
    update: { nome, senhaHash, role },
    create: { email: email.toLowerCase(), nome, senhaHash, role },
  });
  console.log(`✓ Usuário ${role} pronto: ${u.email}`);
}

async function main() {
  await upsertUsuario(
    exigir("ADMIN_EMAIL"),
    process.env.ADMIN_NOME?.trim() || "Advogado",
    exigir("ADMIN_SENHA"),
    "ADMIN",
  );
  await upsertUsuario(
    exigir("CLIENTE_EMAIL"),
    process.env.CLIENTE_NOME?.trim() || "Cliente",
    exigir("CLIENTE_SENHA"),
    "CLIENTE",
  );
}

main()
  .then(() => prisma.$disconnect())
  .catch(async (e) => {
    console.error(e);
    await prisma.$disconnect();
    process.exit(1);
  });
