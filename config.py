"""
config.py — Equity Guard
Configurações centrais do app. Defina ADMIN_EMAIL em .env ou diretamente aqui.
"""

import os
from pathlib import Path

# ── Carrega .env se existir (python-dotenv é opcional) ──────────────────────
try:
    from dotenv import load_dotenv
    _env = Path(__file__).parent / ".env"
    if _env.exists():
        load_dotenv(_env)
except ImportError:
    pass

# ── E-mail do administrador ──────────────────────────────────────────────────
# Configure em .env: ADMIN_EMAIL=seu@email.com
# Ou edite diretamente a linha abaixo como fallback:
# portinho@mac.com tem acesso vitalício — hardcoded como fallback seguro.
# Para sobrescrever, defina ADMIN_EMAIL em .env (útil em deploy).
ADMIN_EMAIL: str = os.getenv("ADMIN_EMAIL", "portinho@mac.com").lower().strip()

# ── Limites de crédito ────────────────────────────────────────────────────────
ANON_QUERY_LIMIT: int = 2       # Consultas sem login — "degustação" antes do cadastro
USER_QUERY_LIMIT: int = 10      # Créditos iniciais após cadastro (modo freemium)
ADMIN_QUERY_LIMIT: int = -1     # -1 = ilimitado

# ── Demo / Lazy-loading ───────────────────────────────────────────────────────
# O ticker padrão carrega sem descontar crédito (cartão de visitas).
DEMO_TICKER: str = "BBAS3"

# ── Taxas de juros (atualização manual baseada em decisões dos BCs) ──────────
# Atualize estes valores após cada decisão do COPOM / FOMC.
SELIC_RATE: float              = 11.25         # % a.a. — última decisão COPOM
SELIC_NEXT_MEETING: str        = "2026-04-30"  # próxima reunião COPOM
FED_FUNDS_RATE: float          = 4.50          # % a.a. — Fed upper bound
FED_NEXT_MEETING: str          = "2026-05-07"  # próxima reunião FOMC

# ── Prevdow — Previdência Complementar (atualização manual mensal) ───────────
# Atualize os valores abaixo copiando do portal oficial uma vez por mês.
PREVDOW_DATA: dict = {
    "url":          "https://www.portalprev.com.br/Prevdow/prevdow/Site/Public/Rentabilidade/",
    "data_base":    "02/2026",          # mês/ano da rentabilidade divulgada
    "cdi_month":    0.93,               # % último mês — Carteira DI
    "balanced_month": 1.60,             # % último mês — Carteira Original Balanceada
    "cdi_year":     2.03,               # % acumulado no ano — Carteira DI
    "balanced_year": 2.94,              # % acumulado no ano — Carteira Original Balanceada
}

# ── Nitro Prev (IFM Previdência / Votorantim) — atualização manual mensal ────
NITRO_DATA: dict = {
    "url":          "https://ifmprev.participante.com.br/login",
    "data_base":    "03/2026",
    # NitroPrev tem 4 perfis: C (Conservador), M (Moderado), A (Arrojado), S (Super)
    # Mantemos 2 campos "cdi/balanced" para compatibilidade visual:
    #   cdi = NitroPrev C (mais conservador)
    #   balanced = NitroPrev M (moderado)
    "cdi_month":    1.16,
    "balanced_month": 0.87,
    "cdi_year":     3.41,
    "balanced_year": 5.85,
    # Perfis adicionais (Arrojado e Super) para exibicao opcional
    "arrojado_month": 0.54,
    "super_month":    0.37,
    "arrojado_year":  8.41,
    "super_year":     9.70,
}

# ── Identidade do app ─────────────────────────────────────────────────────────
APP_NAME: str = "Equity Guard"
APP_TAGLINE: str = "Análise Fundamentalista + Técnica · B3"
APP_ICON: str = "⚡"
APP_VERSION: str = "2.11.0"
