import { hash, verify } from "@node-rs/argon2";

// Hash de senha com argon2id (padrão atual recomendado).
export async function hashPassword(senha: string): Promise<string> {
  return hash(senha);
}

export async function verifyPassword(
  senhaHash: string,
  senha: string,
): Promise<boolean> {
  try {
    return await verify(senhaHash, senha);
  } catch {
    return false;
  }
}

// Política de senha forte: mín. 12 caracteres, com maiúscula, minúscula,
// número e símbolo. Retorna null se válida, ou a mensagem de erro.
export function validarSenhaForte(senha: string): string | null {
  if (senha.length < 12) return "A senha deve ter pelo menos 12 caracteres.";
  if (!/[a-z]/.test(senha)) return "A senha deve conter letra minúscula.";
  if (!/[A-Z]/.test(senha)) return "A senha deve conter letra maiúscula.";
  if (!/[0-9]/.test(senha)) return "A senha deve conter número.";
  if (!/[^A-Za-z0-9]/.test(senha)) return "A senha deve conter símbolo.";
  return null;
}
