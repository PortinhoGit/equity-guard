// Constantes de domínio do caso Durand.

export const EMPRESAS = [
  "Plásticos Barueri",
  "JRPlastic",
  "Plast Log",
  "Pomar",
] as const;

// Navegação principal (uma entrada por grupo de abas).
export const SECOES = [
  { href: "/", label: "Visão executiva", icon: "home" },
  { href: "/cronograma", label: "Cronograma", icon: "calendar" },
  { href: "/clausulas", label: "Cláusulas", icon: "file" },
  { href: "/due-diligence", label: "Due Diligence", icon: "check" },
  { href: "/certidoes", label: "Certidões", icon: "shield" },
  { href: "/contingencias", label: "Contingências", icon: "alert" },
  { href: "/passivos", label: "Passivos", icon: "bank" },
  { href: "/societario", label: "Societário", icon: "users" },
  { href: "/patrimonio", label: "Patrimônio", icon: "box" },
] as const;

export const SECOES_ADMIN = [
  { href: "/exportar", label: "Exportar", icon: "download" },
  { href: "/admin", label: "Auditoria", icon: "log" },
] as const;
