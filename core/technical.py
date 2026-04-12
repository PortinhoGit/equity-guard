"""
core/technical.py
Indicadores técnicos: RSI, Médias Móveis (20/200), Topos/Fundos.
Usa pandas-ta para cálculos robustos.
"""

import pandas as pd
import numpy as np
from typing import Any, Dict, Optional, Tuple

try:
    import pandas_ta as ta
    _HAS_PANDAS_TA = True
except ImportError:
    _HAS_PANDAS_TA = False


# ─── RSI ───────────────────────────────────────────────────────────────────────


def _rsi_manual(series: pd.Series, period: int = 14) -> pd.Series:
    """Cálculo manual de RSI como fallback caso pandas-ta não esteja disponível."""
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1 / period, min_periods=period).mean()
    avg_loss = loss.ewm(alpha=1 / period, min_periods=period).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))


def calculate_rsi(df: pd.DataFrame, period: int = 14) -> Optional[pd.Series]:
    """
    Calcula o RSI.

    Args:
        df: DataFrame com coluna 'Close'
        period: Período do RSI (padrão: 14)

    Returns:
        Series com valores de RSI.
    """
    if df is None or df.empty or "Close" not in df.columns:
        return None
    try:
        if _HAS_PANDAS_TA:
            rsi = ta.rsi(df["Close"], length=period)
        else:
            rsi = _rsi_manual(df["Close"], period=period)
        return rsi
    except Exception:
        return _rsi_manual(df["Close"], period=period)


def get_current_rsi(df: pd.DataFrame, period: int = 14) -> float:
    """Retorna o valor mais recente do RSI. Padrão 50 se não calculável."""
    rsi = calculate_rsi(df, period=period)
    if rsi is None or rsi.empty:
        return 50.0
    val = rsi.dropna().iloc[-1] if not rsi.dropna().empty else 50.0
    return float(val)


# ─── Médias Móveis ─────────────────────────────────────────────────────────────


def calculate_moving_averages(df: pd.DataFrame) -> pd.DataFrame:
    """
    Adiciona MM20 e MM200 ao DataFrame.

    Returns:
        DataFrame com colunas adicionais MA20 e MA200.
    """
    df = df.copy()
    if _HAS_PANDAS_TA:
        df["MA20"] = ta.sma(df["Close"], length=20)
        df["MA200"] = ta.sma(df["Close"], length=200)
    else:
        df["MA20"] = df["Close"].rolling(window=20).mean()
        df["MA200"] = df["Close"].rolling(window=200).mean()
    return df


# ─── Topos e Fundos ────────────────────────────────────────────────────────────


def detect_tops_bottoms(
    df: pd.DataFrame, window: int = 10
) -> Tuple[pd.Series, pd.Series]:
    """
    Detecta topos e fundos locais usando janela deslizante.

    Args:
        df: DataFrame com colunas High e Low
        window: Tamanho da janela de comparação

    Returns:
        (tops, bottoms) — Series com preços nos pivôs, NaN nos demais.
    """
    highs = df["High"]
    lows = df["Low"]
    tops = pd.Series(np.nan, index=df.index)
    bottoms = pd.Series(np.nan, index=df.index)

    for i in range(window, len(df) - window):
        window_highs = highs.iloc[i - window : i + window + 1]
        window_lows = lows.iloc[i - window : i + window + 1]

        if highs.iloc[i] == window_highs.max():
            tops.iloc[i] = highs.iloc[i]

        if lows.iloc[i] == window_lows.min():
            bottoms.iloc[i] = lows.iloc[i]

    return tops.dropna(), bottoms.dropna()


# ─── Análise de Tendência ──────────────────────────────────────────────────────


def analyze_trend(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Avalia a tendência atual com base nas médias móveis.

    Returns:
        Dicionário com análise completa de tendência.
    """
    df_ma = calculate_moving_averages(df)
    current_price = float(df_ma["Close"].iloc[-1])

    ma20_series = df_ma["MA20"].dropna()
    ma200_series = df_ma["MA200"].dropna()

    ma20 = float(ma20_series.iloc[-1]) if not ma20_series.empty else None
    ma200 = float(ma200_series.iloc[-1]) if not ma200_series.empty else None

    trend: Dict[str, Any] = {
        "ma20": ma20,
        "ma200": ma200,
        "short_term": None,
        "long_term": None,
        "golden_cross": False,
        "death_cross": False,
        "overall": "INDEFINIDO",
    }

    if ma20 is not None:
        trend["short_term"] = "ALTA" if current_price > ma20 else "BAIXA"

    if ma200 is not None:
        trend["long_term"] = "ALTA" if current_price > ma200 else "BAIXA"

    if ma20 is not None and ma200 is not None:
        trend["golden_cross"] = ma20 > ma200
        trend["death_cross"] = ma20 < ma200

        if trend["golden_cross"] and trend["short_term"] == "ALTA":
            trend["overall"] = "TENDÊNCIA DE ALTA FORTE"
        elif trend["death_cross"] and trend["short_term"] == "BAIXA":
            trend["overall"] = "TENDÊNCIA DE BAIXA FORTE"
        elif trend["short_term"] == "ALTA":
            trend["overall"] = "TENDÊNCIA DE ALTA"
        else:
            trend["overall"] = "TENDÊNCIA DE BAIXA"

    return trend


# ─── Bandas de Bollinger ───────────────────────────────────────────────────────


def calculate_bollinger_bands(
    df: pd.DataFrame, period: int = 20, std: float = 2.0
) -> Optional[pd.DataFrame]:
    """Calcula as Bandas de Bollinger."""
    if df is None or df.empty:
        return None
    try:
        if _HAS_PANDAS_TA:
            return ta.bbands(df["Close"], length=period, std=std)
        else:
            mid = df["Close"].rolling(window=period).mean()
            sd = df["Close"].rolling(window=period).std()
            bb = pd.DataFrame(index=df.index)
            bb[f"BBU_{period}_{std}"] = mid + std * sd
            bb[f"BBM_{period}_{std}"] = mid
            bb[f"BBL_{period}_{std}"] = mid - std * sd
            return bb
    except Exception:
        return None
