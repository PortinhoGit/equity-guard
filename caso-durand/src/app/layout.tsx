import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Caso Durand — Painel do Contrato",
  description: "Ferramenta interna sigilosa. Acesso restrito.",
  // Reforço de não-indexação além do robots.txt e dos headers.
  robots: {
    index: false,
    follow: false,
    nocache: true,
    googleBot: { index: false, follow: false },
  },
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="pt-BR" className="h-full antialiased">
      <body className="min-h-full">{children}</body>
    </html>
  );
}
