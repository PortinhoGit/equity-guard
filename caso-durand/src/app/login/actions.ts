"use server";

import { AuthError } from "next-auth";
import { signIn } from "@/auth";

export async function autenticar(
  _prev: string | undefined,
  formData: FormData,
): Promise<string | undefined> {
  try {
    await signIn("credentials", {
      email: formData.get("email"),
      senha: formData.get("senha"),
      redirectTo: "/",
    });
  } catch (error) {
    if (error instanceof AuthError) {
      return "E-mail ou senha inválidos.";
    }
    // signIn lança um redirect em caso de sucesso — repassar.
    throw error;
  }
}
