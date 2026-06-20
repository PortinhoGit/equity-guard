import type { NextAuthConfig } from "next-auth";
import type { Role } from "@prisma/client";

// Configuração compartilhada e segura para o Edge (usada pelo middleware).
// NÃO importa Prisma nem argon2 (não rodam no Edge runtime).
export const authConfig = {
  pages: {
    signIn: "/login",
  },
  session: {
    strategy: "jwt",
    maxAge: 8 * 60 * 60, // sessão curta: 8 horas, depois re-login
  },
  trustHost: true,
  callbacks: {
    // Protege todas as rotas: só passa quem tem sessão válida.
    authorized({ auth, request: { nextUrl } }) {
      const logado = !!auth?.user;
      const naLogin = nextUrl.pathname.startsWith("/login");
      if (naLogin) {
        if (logado) return Response.redirect(new URL("/", nextUrl));
        return true;
      }
      return logado;
    },
    jwt({ token, user }) {
      if (user) {
        token.id = user.id as string;
        token.role = user.role;
      }
      return token;
    },
    session({ session, token }) {
      if (session.user) {
        session.user.id = token.id ? String(token.id) : "";
        if (token.role) session.user.role = token.role as Role;
      }
      return session;
    },
  },
  providers: [], // providers reais ficam em auth.ts (runtime Node)
} satisfies NextAuthConfig;
