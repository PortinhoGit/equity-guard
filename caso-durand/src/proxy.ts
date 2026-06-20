import NextAuth from "next-auth";
import { authConfig } from "./auth.config";

// Proxy de autenticação (antigo "middleware"): protege todas as rotas
// via o callback `authorized` definido em auth.config.
export const proxy = NextAuth(authConfig).auth;
export default proxy;

export const config = {
  // Roda em tudo, exceto assets estáticos, a API de auth e arquivos públicos.
  matcher: [
    "/((?!api/auth|_next/static|_next/image|favicon.ico|robots.txt|sitemap.xml).*)",
  ],
};
