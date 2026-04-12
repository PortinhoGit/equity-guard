"""
core/valuation.py — Equity Guard
Lógica de valuação: Preço Teto, Margem de Segurança, Saúde Financeira e Sinal de Compra.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, Tuple


# ─── Setores BEST ──────────────────────────────────────────────────────────────

BEST_KEYWORDS: Dict[str, list] = {
    "Bancos": [
        "bank", "banco", "financ", "credit", "crédito", "itaú", "bradesco",
        "santander", "btg", "inter", "nubank",
    ],
    "Energia": [
        "energy", "energia", "electric", "elétric", "power", "petróleo",
        "oil", "gas", "gás", "combustível", "fuel", "utilities", "geração",
        "transmissão", "eletrobras", "cemig", "copel", "engie", "taesa",
    ],
    "Saneamento": [
        "sanit", "water", "água", "sewer", "esgoto", "sabesp", "copasa",
        "sanepar", "aegea",
    ],
    "Telecom": [
        "telecom", "communic", "comunicação", "wireless", "phone", "telefon",
        "tim", "vivo", "claro", "oi", "internet",
    ],
    "Seguros": [
        "insur", "segur", "seguros", "previdência", "life", "saúde", "health",
        "porto", "bb seguridade", "caixa seguridade",
    ],
}


def identify_best_sector(sector: str, industry: str) -> Tuple[bool, str]:
    """
    Identifica se o ticker pertence aos setores BEST (Barsi).

    Args:
        sector: Setor informado pelo yfinance
        industry: Subsetor/indústria informado pelo yfinance

    Returns:
        (is_best: bool, sector_name: str)
    """
    text = f"{sector} {industry}".lower()
    for sector_name, keywords in BEST_KEYWORDS.items():
        if any(kw in text for kw in keywords):
            return True, sector_name
    return False, "Outro"


# ─── Dividendos ────────────────────────────────────────────────────────────────


def calculate_avg_dividends(dividends: pd.Series, years: int = 5) -> float:
    """
    Calcula a média anual de dividendos dos últimos N anos.

    Args:
        dividends: Series com histórico de proventos
        years: Número de anos a considerar

    Returns:
        Média anual de dividendos em R$.
    """
    if dividends is None or dividends.empty:
        return 0.0

    try:
        # Agrupa por ano e soma os proventos
        annual = dividends.resample("YE").sum()
        annual = annual[annual > 0]
        if annual.empty:
            return 0.0
        return float(annual.tail(years).mean())
    except Exception:
        return float(dividends.sum() / max(years, 1))


def calculate_teto_barsi(avg_annual_dividends: float, target_yield: float = 0.06) -> float:
    """
    Calcula o Preço Teto Barsi.

    Fórmula: Teto = Dividendo Médio Anual / Yield Alvo

    Args:
        avg_annual_dividends: Média de dividendos anuais (R$)
        target_yield: Yield desejado como decimal (ex: 0.06 = 6%)

    Returns:
        Preço teto em R$, ou 0.0 se não calculável.
    """
    if avg_annual_dividends <= 0 or target_yield <= 0:
        return 0.0
    return avg_annual_dividends / target_yield


def calculate_safety_margin(current_price: float, teto_price: float) -> float:
    """
    Calcula a Margem de Segurança em relação ao Preço Teto.

    Positivo = abaixo do teto (bom / compra)
    Negativo = acima do teto (caro / risco)

    Returns:
        Margem de segurança em percentual.
    """
    if teto_price <= 0 or current_price <= 0:
        return 0.0
    return ((teto_price - current_price) / teto_price) * 100


def project_dividends(
    avg_annual_dividends: float,
    years: int = 5,
    growth_rate: float = 0.05,
) -> Dict[int, float]:
    """
    Projeta dividendos futuros com taxa de crescimento composta.

    Args:
        avg_annual_dividends: Base anual de dividendos
        years: Horizonte de projeção
        growth_rate: Taxa de crescimento anual (ex: 0.05 = 5%)

    Returns:
        Dicionário {ano_relativo: dividendo_projetado}
    """
    return {
        year: avg_annual_dividends * ((1 + growth_rate) ** year)
        for year in range(1, years + 1)
    }


# ─── Saúde Financeira ──────────────────────────────────────────────────────────


def check_health_indicators(fundamentals: Dict[str, Any]) -> Dict[str, Any]:
    """
    Avalia os indicadores de saúde financeira com base nos critérios de valor.

    Critérios:
        - Payout: 40% a 80%
        - Dívida Líquida / EBITDA: < 3.0
        - ROE: > 15%

    Returns:
        Dicionário com status e valores de cada indicador.
    """
    health: Dict[str, Any] = {
        "payout_ok": None,
        "payout_value": None,
        "debt_ebitda_ok": None,
        "debt_ebitda_value": None,
        "roe_ok": None,
        "roe_value": None,
    }

    # ── Payout ────────────────────────────────────────────────────────────────
    payout = fundamentals.get("payout_ratio")
    if payout is not None and not np.isnan(float(payout)):
        payout_pct = float(payout) * 100
        health["payout_value"] = payout_pct
        health["payout_ok"] = 40.0 <= payout_pct <= 80.0

    # ── Dívida Líq. / EBITDA ─────────────────────────────────────────────────
    nd_ebitda = fundamentals.get("net_debt_ebitda")
    if nd_ebitda is not None and not np.isnan(float(nd_ebitda)):
        health["debt_ebitda_value"] = float(nd_ebitda)
        health["debt_ebitda_ok"] = float(nd_ebitda) < 3.0

    # ── ROE ───────────────────────────────────────────────────────────────────
    roe = fundamentals.get("roe")
    if roe is not None and not np.isnan(float(roe)):
        roe_pct = float(roe) * 100
        health["roe_value"] = roe_pct
        health["roe_ok"] = roe_pct > 15.0

    return health


# ─── Sinal de Compra Híbrido ───────────────────────────────────────────────────


def generate_buy_signal(
    current_price: float,
    teto_price: float,
    rsi: float,
) -> Dict[str, str]:
    """
    Gera sinal de compra baseado em Preço Teto + RSI.

    Regras:
        strong_buy → Preço < Teto AND RSI < 35
        buy        → Preço < Teto AND 35 ≤ RSI ≤ 70
        wait       → Preço < Teto AND RSI > 70  (sobrecomprado)
        neutral    → Preço ≥ Teto AND RSI < 70
        avoid      → Preço ≥ Teto AND RSI ≥ 70

    Returns:
        {signal_key, color, bg_color, emoji}
        O campo 'signal_key' é usado pela camada de UI para traduzir o rótulo.
    """
    below_teto = teto_price > 0 and current_price < teto_price

    if below_teto and rsi < 35:
        return {
            "signal_key": "strong_buy",
            "color":      "#3fb950",
            "bg_color":   "rgba(63,185,80,0.15)",
            "emoji":      "🟢",
        }
    elif below_teto and rsi <= 70:
        return {
            "signal_key": "buy",
            "color":      "#56d364",
            "bg_color":   "rgba(63,185,80,0.08)",
            "emoji":      "🟩",
        }
    elif below_teto and rsi > 70:
        return {
            "signal_key": "wait",
            "color":      "#e3b341",
            "bg_color":   "rgba(227,179,65,0.12)",
            "emoji":      "🟡",
        }
    elif not below_teto and rsi >= 70:
        return {
            "signal_key": "avoid",
            "color":      "#f85149",
            "bg_color":   "rgba(248,81,73,0.15)",
            "emoji":      "🔴",
        }
    else:
        return {
            "signal_key": "neutral",
            "color":      "#8b949e",
            "bg_color":   "rgba(139,148,158,0.10)",
            "emoji":      "⚪",
        }
