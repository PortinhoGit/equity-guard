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
    "cdi_month":    0.92,               # % último mês — Perfil CDI
    "balanced_month": 1.34,             # % último mês — Perfil Balanceado
    "cdi_year":     2.81,               # % acumulado no ano — Perfil CDI
    "balanced_year": 3.52,              # % acumulado no ano — Perfil Balanceado
}

# ── Nitro Prev (IFM Previdência / Votorantim) — atualização manual mensal ────
NITRO_DATA: dict = {
    "url":          "https://ifmprev.participante.com.br/login",
    "data_base":    "N/D",
    "cdi_month":    None,
    "balanced_month": None,
    "cdi_year":     None,
    "balanced_year": None,
}

# ── Identidade do app ─────────────────────────────────────────────────────────
APP_NAME: str = "Equity Guard"
APP_TAGLINE: str = "Análise Fundamentalista + Técnica · B3"
APP_ICON: str = "⚡"
APP_VERSION: str = "2.1.0"
