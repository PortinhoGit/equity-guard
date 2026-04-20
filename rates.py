"""
rates.py — Equity Guard
Busca automatica de taxas de juros e proximas reunioes.

Estrategia:
  * Selic vigente  -> BCB SGS API (serie 432), cache 6h, fallback config.
  * Fed Funds      -> config.py (manual), com aviso de desatualizado.
  * COPOM meeting  -> calendario hardcoded, helper retorna proxima futura.
  * FOMC meeting   -> calendario hardcoded, helper retorna proxima futura.

BCB API e publica sem autenticacao. FRED/Fed bloqueados do nosso ambiente,
entao ficam manuais por enquanto (manutencao ~8x/ano).
"""

from datetime import date, datetime
from typing import Optional, Tuple, List

# ═══ Calendario oficial COPOM 2026 (datas de DECISAO, geralmente quarta) ════
# Fonte: https://www.bcb.gov.br/publicacoes/calendarioreunioescopom
COPOM_2026: List[date] = [
    date(2026, 1, 28),
    date(2026, 3, 18),
    date(2026, 4, 29),
    date(2026, 6, 17),
    date(2026, 7, 29),
    date(2026, 9, 16),
    date(2026, 11, 4),
    date(2026, 12, 9),
]
COPOM_2027: List[date] = [
    date(2027, 1, 27),
    date(2027, 3, 17),
    date(2027, 5, 5),
    date(2027, 6, 16),
    date(2027, 7, 28),
    date(2027, 9, 15),
    date(2027, 11, 3),
    date(2027, 12, 8),
]

# ═══ Calendario oficial FOMC 2026 (datas de DECISAO, geralmente quarta) ═════
# Fonte: https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm
FOMC_2026: List[date] = [
    date(2026, 1, 28),
    date(2026, 3, 18),
    date(2026, 4, 29),
    date(2026, 6, 17),
    date(2026, 7, 29),
    date(2026, 9, 16),
    date(2026, 11, 4),
    date(2026, 12, 9),
]
FOMC_2027: List[date] = [
    date(2027, 1, 27),
    date(2027, 3, 17),
    date(2027, 4, 28),
    date(2027, 6, 16),
    date(2027, 7, 28),
    date(2027, 9, 15),
    date(2027, 11, 3),
    date(2027, 12, 15),
]


def _next_upcoming(calendar: List[date], today: Optional[date] = None) -> Optional[date]:
    """Primeira data futura ou de hoje na lista (ordenada)."""
    today = today or date.today()
    for d in sorted(calendar):
        if d >= today:
            return d
    return None


# ═══ Selic via BCB SGS (cache 6h) ═════════════════════════════════════════════

_selic_cache: dict = {"value": None, "fetched_at": None}


def get_selic(fallback: float = 14.75) -> Tuple[float, str]:
    """
    Retorna (taxa_selic_em_percent, fonte).
    Fonte = 'bcb' (auto-fetch bem-sucedido) ou 'config' (fallback).
    Cache em memoria por 6h.
    """
    now = datetime.now()
    cached = _selic_cache.get("value")
    fetched = _selic_cache.get("fetched_at")
    if cached is not None and fetched and (now - fetched).total_seconds() < 6 * 3600:
        return cached, _selic_cache.get("source", "bcb")

    try:
        import requests
        r = requests.get(
            "https://api.bcb.gov.br/dados/serie/bcdata.sgs.432/dados/ultimos/1?formato=json",
            timeout=10,
        )
        r.raise_for_status()
        rows = r.json()
        if rows and "valor" in rows[0]:
            val = float(rows[0]["valor"])
            _selic_cache.update({"value": val, "fetched_at": now, "source": "bcb"})
            return val, "bcb"
    except Exception:
        pass

    _selic_cache.update({"value": fallback, "fetched_at": now, "source": "config"})
    return fallback, "config"


# ═══ Helpers de datas de reuniao ══════════════════════════════════════════════

def next_copom(today: Optional[date] = None) -> Optional[date]:
    all_dates = COPOM_2026 + COPOM_2027
    return _next_upcoming(all_dates, today)


def next_fomc(today: Optional[date] = None) -> Optional[date]:
    all_dates = FOMC_2026 + FOMC_2027
    return _next_upcoming(all_dates, today)


# ═══ Sinal de atualizacao manual pendente ═════════════════════════════════════

def fed_needs_manual_update(fed_next_meeting: str, tolerance_days: int = 7) -> bool:
    """
    True se a FED_NEXT_MEETING no config ja passou ha mais de N dias,
    indicando que o operador precisa atualizar o FED_FUNDS_RATE manualmente.
    """
    try:
        d = datetime.strptime(fed_next_meeting, "%Y-%m-%d").date()
    except Exception:
        return False
    today = date.today()
    return (today - d).days > tolerance_days
