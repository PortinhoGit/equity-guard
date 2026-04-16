"""
data/provider.py
Integração com yfinance para buscar dados de ações brasileiras (B3).
Trata automaticamente a conversão de tickers (ex: PETR4 -> PETR4.SA).
"""

import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Tuple
import logging

logger = logging.getLogger(__name__)


def normalize_ticker(ticker: str) -> str:
    """
    Normaliza o ticker para o formato yfinance, suportando múltiplos mercados:

    - Já contém '.' (ex: PETR4.SA, HSBA.L, AIR.PA): retorna como está
    - Termina em dígito (ex: PETR4, BBAS3, TAEE11): assume B3 e adiciona .SA
    - Apenas letras (ex: AAPL, MSFT, KO, SCHD): assume EUA, retorna como está
    """
    ticker = ticker.upper().strip()
    if not ticker:
        return ticker
    if "." in ticker:
        return ticker
    if ticker[-1].isdigit():
        return f"{ticker}.SA"
    return ticker


def get_stock_data(ticker: str, period: str = "2y") -> Optional[pd.DataFrame]:
    """
    Busca histórico de preços OHLCV.

    Args:
        ticker: Código da ação (ex: PETR4 ou PETR4.SA)
        period: Período de histórico (1y, 2y, 3y, 5y)

    Returns:
        DataFrame com OHLCV ou None em caso de erro.
    """
    ticker_sa = normalize_ticker(ticker)
    try:
        stock = yf.Ticker(ticker_sa)
        df = stock.history(period=period, auto_adjust=True)
        if df.empty:
            logger.warning(f"Sem dados de preço para {ticker_sa}")
            return None
        df.index = pd.to_datetime(df.index)
        # Remove timezone para compatibilidade
        if df.index.tz is not None:
            df.index = df.index.tz_localize(None)
        return df
    except Exception as e:
        logger.error(f"Erro ao buscar preços para {ticker_sa}: {e}")
        return None


def get_dividends(ticker: str, years: int = 5) -> Optional[pd.Series]:
    """
    Busca histórico de proventos dos últimos N anos.

    Nota sobre splits: yfinance já retorna os dividendos históricos
    normalizados para a base acionária atual. Investigação empírica com BBAS3
    (split 1:2 em abril/2024) confirmou que os valores pré-split em
    stock.dividends já estão na base da nova ação — aplicar correção manual
    causaria duplo ajuste. A correção do DY distorcido (ex: 113%) é feita em
    get_full_data() substituindo info['dividendYield'] pelo cálculo próprio
    de Trailing-12M Yield.

    Args:
        ticker: Código da ação (ex: PETR4 ou PETR4.SA)
        years:  Anos de histórico

    Returns:
        Series com datas e valores de dividendos, ou None.
    """
    ticker_sa = normalize_ticker(ticker)
    try:
        stock = yf.Ticker(ticker_sa)
        dividends = stock.dividends

        if dividends.empty:
            logger.warning(f"Sem dados de dividendos para {ticker_sa}")
            return None

        # Normaliza timezone
        if dividends.index.tz is not None:
            dividends.index = dividends.index.tz_localize(None)

        # Filtra os últimos N anos e remove valores inválidos
        cutoff = datetime.now() - timedelta(days=years * 365)
        dividends = dividends[(dividends.index >= cutoff) & (dividends > 0)]

        return dividends if not dividends.empty else None

    except Exception as e:
        logger.error(f"Erro ao buscar dividendos para {ticker_sa}: {e}")
        return None


def get_fundamentals(ticker: str) -> Dict[str, Any]:
    """
    Busca dados fundamentalistas via yfinance.
    Inclui fallbacks para campos ausentes em ações da B3.

    Args:
        ticker: Código da ação

    Returns:
        Dicionário com métricas fundamentalistas.
    """
    ticker_sa = normalize_ticker(ticker)
    try:
        stock = yf.Ticker(ticker_sa)
        info = stock.info

        if not info or info.get("regularMarketPrice") is None and info.get("currentPrice") is None:
            logger.warning(f"Info vazia ou inválida para {ticker_sa}")
            return _empty_fundamentals(ticker)

        # Preço atual com múltiplos fallbacks
        current_price = (
            info.get("currentPrice")
            or info.get("regularMarketPrice")
            or info.get("previousClose")
        )

        # ROE: yfinance retorna como decimal (ex: 0.18 = 18%)
        roe_raw = info.get("returnOnEquity")

        # Payout: yfinance retorna como decimal
        payout_raw = info.get("payoutRatio")

        # Dividend yield
        dy_raw = info.get("dividendYield") or info.get("trailingAnnualDividendYield")

        # Dívida e EBITDA
        total_debt = info.get("totalDebt") or 0
        total_cash = info.get("totalCash") or info.get("cashAndCashEquivalents") or 0
        ebitda = info.get("ebitda")

        net_debt = total_debt - total_cash if total_debt else None
        net_debt_ebitda = None
        if net_debt is not None and ebitda and ebitda != 0:
            net_debt_ebitda = net_debt / ebitda

        fundamentals = {
            "name": info.get("longName") or info.get("shortName") or ticker,
            "sector": info.get("sector") or "Desconhecido",
            "industry": info.get("industry") or "",
            "current_price": current_price,
            "market_cap": info.get("marketCap"),
            "pe_ratio": info.get("trailingPE") or info.get("forwardPE"),
            "pb_ratio": info.get("priceToBook"),
            "roe": roe_raw,
            "dividend_yield": dy_raw,
            "payout_ratio": payout_raw,
            "net_debt": net_debt,
            "ebitda": ebitda,
            "total_debt": total_debt,
            "total_cash": total_cash,
            "net_debt_ebitda": net_debt_ebitda,
            "shares_outstanding": info.get("sharesOutstanding"),
            "currency": info.get("currency", "BRL"),
            "exchange": info.get("exchange", "SAO"),
        }

        return fundamentals

    except Exception as e:
        logger.error(f"Erro ao buscar fundamentais para {ticker_sa}: {e}")
        return _empty_fundamentals(ticker)


def _empty_fundamentals(ticker: str) -> Dict[str, Any]:
    """Retorna estrutura vazia de fundamentais para evitar KeyError."""
    return {
        "name": ticker,
        "sector": "Desconhecido",
        "industry": "",
        "current_price": None,
        "market_cap": None,
        "pe_ratio": None,
        "pb_ratio": None,
        "roe": None,
        "dividend_yield": None,
        "payout_ratio": None,
        "net_debt": None,
        "ebitda": None,
        "total_debt": None,
        "total_cash": None,
        "net_debt_ebitda": None,
        "shares_outstanding": None,
        "currency": "BRL",
        "exchange": "SAO",
    }


def get_price_performance(df: pd.DataFrame) -> dict:
    """
    Calcula métricas de performance de preço em múltiplos horizontes.

    Args:
        df: DataFrame OHLCV com índice DatetimeIndex

    Returns:
        Dict com: current, yesterday, chg_1d, price_7d, chg_7d,
                  price_30d, chg_30d, price_52w, chg_52w, w52_min, w52_max
    """
    if df is None or df.empty or len(df) < 2:
        return {}

    close   = df["Close"]
    current = float(close.iloc[-1])
    now_idx = df.index[-1]

    def _lookback(days: int) -> Optional[float]:
        cutoff = now_idx - pd.Timedelta(days=days)
        past   = close[close.index <= cutoff]
        return float(past.iloc[-1]) if not past.empty else None

    def _pct(prev: Optional[float]) -> Optional[float]:
        if prev is None or prev == 0:
            return None
        return (current - prev) / prev * 100

    yesterday = float(close.iloc[-2]) if len(close) >= 2 else None
    p7d  = _lookback(7)
    p30d = _lookback(30)
    p52w = _lookback(365)

    window_52w = close[close.index >= (now_idx - pd.Timedelta(days=365))]
    w52_min = float(window_52w.min()) if not window_52w.empty else float(close.min())
    w52_max = float(window_52w.max()) if not window_52w.empty else float(close.max())

    return {
        "current":   current,
        "yesterday": yesterday,
        "chg_1d":    _pct(yesterday),
        "price_7d":  p7d,
        "chg_7d":    _pct(p7d),
        "price_30d": p30d,
        "chg_30d":   _pct(p30d),
        "price_52w": p52w,
        "chg_52w":   _pct(p52w),
        "w52_min":   w52_min,
        "w52_max":   w52_max,
    }


_GLOBAL_TICKERS = [
    # (display_name, yfinance_symbol, locale_hint)
    ("IBOV",    "^BVSP",  "br"),
    ("S&P 500", "^GSPC",  "us"),
    ("NASDAQ",  "^IXIC",  "us"),
    ("FTSE",    "^FTSE",  "us"),
    ("Brent",   "BZ=F",   "us"),
    ("WTI",     "CL=F",   "us"),
]


def get_global_indicators() -> list:
    """
    Busca o último fechamento + variação diária % dos principais índices
    globais e commodities de energia.
    Retorna lista de dicts: {name, symbol, locale, last, change}.
    Valores None quando o fetch falha (não quebra o painel).
    """
    results = []
    for name, sym, locale in _GLOBAL_TICKERS:
        entry = {"name": name, "symbol": sym, "locale": locale,
                 "last": None, "change": None}
        try:
            tk = yf.Ticker(sym)
            hist = tk.history(period="5d", interval="1d", auto_adjust=True)
            if hist is None or hist.empty:
                results.append(entry)
                continue
            closes = hist["Close"].dropna()
            if len(closes) < 2:
                results.append(entry)
                continue
            last = float(closes.iloc[-1])
            prev = float(closes.iloc[-2])
            entry["last"]   = last
            entry["change"] = ((last - prev) / prev * 100) if prev else 0.0
        except Exception as e:
            logger.error(f"global indicator {sym} failed: {e}")
        results.append(entry)
    return results


def get_fx_usdbrl() -> Optional[Dict[str, Any]]:
    """
    Cotação USD/BRL comercial + turismo, histórico 7d do comercial.
    BCB PTAX para comercial; turismo = comercial * spread (~4%).
    """
    import requests as _req

    bid = ask = None
    # ── BCB PTAX (comercial) ─────────────────────────────────────────────────
    try:
        _today = pd.Timestamp.now().strftime("%m-%d-%Y")
        _url = (
            "https://olinda.bcb.gov.br/olinda/servico/PTAX/versao/v1/odata/"
            f"CotacaoDolarDia(dataCotacao=@d)?@d='{_today}'"
            "&$top=1&$orderby=dataHoraCotacao%20desc&$format=json"
        )
        r = _req.get(_url, timeout=5)
        if r.ok:
            data = r.json().get("value", [])
            if data:
                bid = float(data[0]["cotacaoCompra"])
                ask = float(data[0]["cotacaoVenda"])
    except Exception as e:
        logger.warning(f"BCB PTAX falhou: {e}")

    # ── yfinance (comercial) + sparkline ─────────────────────────────────────
    try:
        tk = yf.Ticker("USDBRL=X")
        hist = tk.history(period="1mo", interval="1d", auto_adjust=True)
        if hist is None or hist.empty:
            if bid is None:
                return None
            hist_ok = False
        else:
            hist_ok = True
    except Exception as e:
        logger.error(f"Erro ao buscar USDBRL=X: {e}")
        if bid is None:
            return None
        hist_ok = False

    series = None
    if hist_ok:
        closes = hist["Close"].dropna()
        if closes.index.tz is not None:
            closes.index = closes.index.tz_localize(None)
        if len(closes) >= 2:
            series = closes.tail(7)
            if ask is None:
                ask = float(series.iloc[-1])
            if bid is None:
                bid = round(ask * 0.995, 4)

    if ask is None:
        return None
    if bid is None:
        bid = round(ask * 0.995, 4)

    prev = float(series.iloc[-2]) if series is not None and len(series) >= 2 else ask
    chg = ((ask - prev) / prev * 100) if prev else 0.0

    TURISMO_SPREAD = 0.04
    tur_bid = round(bid * (1 + TURISMO_SPREAD), 4)
    tur_ask = round(ask * (1 + TURISMO_SPREAD), 4)
    prev_tur = round(prev * (1 + TURISMO_SPREAD), 4)

    return {
        "com_bid": bid, "com_ask": ask, "com_prev": prev,
        "tur_bid": tur_bid, "tur_ask": tur_ask, "tur_prev": prev_tur,
        "change": chg, "series": series,
        "last": ask, "prev": prev,
        "fetched_at": pd.Timestamp.now(tz="America/Sao_Paulo").tz_localize(None),
    }


def get_stock_history(ticker: str, period: str) -> Optional[pd.DataFrame]:
    """
    Histórico de preços para um período específico (gráfico interativo).
    Seleciona o intervalo automaticamente para manter a granularidade ideal:

        1d  → 5 min      6mo → 1 dia      ytd → 1 dia
        5d  → 15 min     1y  → 1 dia
        1mo → 1 dia      5y  → 1 semana

    Aceita os mesmos códigos de período do yfinance.
    """
    interval_map = {
        "1d":  "5m",
        "5d":  "15m",
        "1mo": "1d",
        "6mo": "1d",
        "1y":  "1d",
        "5y":  "1wk",
        "ytd": "1d",
    }
    interval = interval_map.get(period, "1d")
    ticker_sa = normalize_ticker(ticker)
    try:
        stock = yf.Ticker(ticker_sa)
        df = stock.history(period=period, interval=interval, auto_adjust=True)
        if df.empty:
            return None
        df.index = pd.to_datetime(df.index)
        if df.index.tz is not None:
            df.index = df.index.tz_localize(None)
        return df
    except Exception as e:
        logger.error(f"Erro ao buscar histórico {ticker_sa}/{period}/{interval}: {e}")
        return None


def detect_dividend_frequency(dividends: Optional[pd.Series]) -> Dict[str, Any]:
    """
    Classifica a periodicidade de pagamento de dividendos baseada nos
    últimos 24 meses de histórico.

    Retorna dict com:
        key:         'monthly' | 'quarterly' | 'semiannual' | 'annual'
                     | 'irregular' | 'none'
        payments_12m: nº de pagamentos nos últimos 12 meses
        avg_gap_days: mediana do intervalo entre pagamentos (24m), ou None
        cycle_months: list[int] dos meses do ciclo identificado, ou None
    """
    empty = {"key": "none", "payments_12m": 0, "avg_gap_days": None, "cycle_months": None}
    if dividends is None or dividends.empty:
        return empty

    now = pd.Timestamp.now()
    last_12m = dividends[dividends.index >= (now - pd.Timedelta(days=365))]
    pay_12m  = int(len(last_12m))

    if pay_12m == 0:
        return empty

    last_24m = dividends[dividends.index >= (now - pd.Timedelta(days=730))]
    if len(last_24m) < 2:
        return {"key": "irregular", "payments_12m": pay_12m,
                "avg_gap_days": None, "cycle_months": None}

    gaps = last_24m.index.sort_values().to_series().diff().dropna().dt.days
    median_gap = float(gaps.median()) if not gaps.empty else None

    if pay_12m >= 10 or (median_gap is not None and median_gap <= 45):
        key = "monthly"
    elif median_gap is not None and median_gap <= 120:
        key = "quarterly"
    elif median_gap is not None and median_gap <= 240:
        key = "semiannual"
    elif median_gap is not None and median_gap <= 450:
        key = "annual"
    else:
        key = "irregular"

    cycle_months = sorted({int(d.month) for d in last_24m.index})
    return {
        "key": key,
        "payments_12m": pay_12m,
        "avg_gap_days": median_gap,
        "cycle_months": cycle_months,
    }


def get_dividend_month_pattern(dividends: Optional[pd.Series]) -> Dict[int, int]:
    """
    Conta quantos pagamentos históricos ocorreram em cada mês do ano (1-12).
    Útil para construir o mapa mensal de proventos (heatmap Jan-Dez).
    """
    if dividends is None or dividends.empty:
        return {m: 0 for m in range(1, 13)}
    months = dividends.index.month
    return {m: int((months == m).sum()) for m in range(1, 13)}


def get_dividend_calendar(ticker: str, n: int = 15) -> pd.DataFrame:
    """
    Retorna calendário de proventos com Data-COM, Data-Ex e status.

    Em bolsas brasileiras:
        Data-COM  = último dia para comprar e ter direito ao provento
        Data-Ex   = primeiro dia negociado sem o provento (ex-dividend date)
        yfinance indexa os dividendos pela Data-Ex; calculamos
        Data-COM = Data-Ex − 1 dia útil.

    Args:
        ticker: Código da ação (ex: PETR4 ou PETR4.SA)
        n: Número de registros históricos a retornar

    Returns:
        DataFrame com colunas:
            type, com_date, ex_date, payment_date, value, status, days_until_com
    """
    ticker_sa = normalize_ticker(ticker)
    try:
        stock = yf.Ticker(ticker_sa)
        divs  = stock.dividends

        if divs is None or divs.empty:
            logger.warning(f"stock.dividends vazio no calendário para {ticker_sa}, tentando fallback")
            raw = stock.history(period="5y", auto_adjust=True)
            if not raw.empty and "Dividends" in raw.columns:
                divs = raw["Dividends"]
                divs = divs[divs > 0]
            else:
                return pd.DataFrame()

        if divs.empty:
            return pd.DataFrame()

        if divs.index.tz is not None:
            divs.index = divs.index.tz_localize(None)

        today = pd.Timestamp.now().normalize()
        rows: list = []

        for ex_date, value in divs[divs > 0].tail(n).items():
            ex_ts  = pd.Timestamp(ex_date).normalize()
            com_ts = ex_ts - pd.offsets.BDay(1)
            status = "paid" if ex_ts < today else "provisioned"
            days_until_com: Optional[int] = (
                int((com_ts - today).days) if com_ts >= today else None
            )
            rows.append({
                "type":           "Div/JCP",
                "com_date":       com_ts,
                "ex_date":        ex_ts,
                "payment_date":   None,
                "value":          float(value),
                "status":         status,
                "days_until_com": days_until_com,
            })

        if not rows:
            return pd.DataFrame()

        df_cal = (
            pd.DataFrame(rows)
            .sort_values("ex_date", ascending=False)
            .reset_index(drop=True)
        )
        return df_cal

    except Exception as e:
        logger.error(f"Erro ao buscar calendário para {ticker_sa}: {e}")
        return pd.DataFrame()


def get_full_data(ticker: str, period: str = "2y") -> Tuple[
    Optional[pd.DataFrame],
    Optional[pd.Series],
    Dict[str, Any],
]:
    """
    Busca todos os dados necessários para análise em uma única chamada.

    Inclui correção de Dividend Yield: substitui o valor bugado do
    info['dividendYield'] (que pode ficar distorcido após splits, como os
    113% do BBAS3) pelo Trailing-12-Month Yield calculado diretamente dos
    proventos ajustados:  DY = Σ dividendos (últimos 365 dias) / preço atual.

    Returns:
        Tupla (df_precos, dividendos_ajustados, fundamentais)
    """
    ticker_sa = normalize_ticker(ticker)
    stock = yf.Ticker(ticker_sa)

    # ── 1. Preços ────────────────────────────────────────────────────────────
    df = None
    try:
        raw = stock.history(period=period, auto_adjust=True)
        if not raw.empty:
            raw.index = pd.to_datetime(raw.index)
            if raw.index.tz is not None:
                raw.index = raw.index.tz_localize(None)
            df = raw
    except Exception as e:
        logger.error(f"Erro ao buscar preços para {ticker_sa}: {e}")

    # ── 2. Dividendos — tenta stock.dividends e history(5y), usa o mais completo
    dividends = None
    divs_primary = None
    divs_fallback = None

    try:
        divs = stock.dividends
        if divs is not None and not divs.empty:
            if divs.index.tz is not None:
                divs.index = divs.index.tz_localize(None)
            cutoff = datetime.now() - timedelta(days=5 * 365)
            divs = divs[(divs.index >= cutoff) & (divs > 0)]
            if not divs.empty:
                divs_primary = divs
    except Exception as e:
        logger.warning(f"stock.dividends falhou para {ticker_sa}: {e}")

    try:
        raw_5y = stock.history(period="5y", auto_adjust=True)
        if not raw_5y.empty and "Dividends" in raw_5y.columns:
            fb = raw_5y["Dividends"]
            fb = fb[fb > 0]
            if fb.index.tz is not None:
                fb.index = fb.index.tz_localize(None)
            if not fb.empty:
                divs_fallback = fb
    except Exception as e:
        logger.warning(f"history(5y) falhou para {ticker_sa}: {e}")

    if divs_primary is not None and divs_fallback is not None:
        dividends = divs_primary if len(divs_primary) >= len(divs_fallback) else divs_fallback
    else:
        dividends = divs_primary or divs_fallback

    if dividends is not None:
        logger.info(f"Dividendos para {ticker_sa}: {len(dividends)} registros, soma={dividends.sum():.2f}")

    # ── 3. Fundamentais ──────────────────────────────────────────────────────
    fundamentals = _empty_fundamentals(ticker)
    try:
        info = stock.info
        if info and (info.get("regularMarketPrice") is not None or info.get("currentPrice") is not None):
            current_price = (
                info.get("currentPrice")
                or info.get("regularMarketPrice")
                or info.get("previousClose")
            )
            roe_raw = info.get("returnOnEquity")
            payout_raw = info.get("payoutRatio")
            dy_raw = info.get("dividendYield") or info.get("trailingAnnualDividendYield")
            total_debt = info.get("totalDebt") or 0
            total_cash = info.get("totalCash") or info.get("cashAndCashEquivalents") or 0
            ebitda = info.get("ebitda")
            net_debt = total_debt - total_cash if total_debt else None
            net_debt_ebitda = None
            if net_debt is not None and ebitda and ebitda != 0:
                net_debt_ebitda = net_debt / ebitda

            fundamentals = {
                "name": info.get("longName") or info.get("shortName") or ticker,
                "sector": info.get("sector") or "Desconhecido",
                "industry": info.get("industry") or "",
                "current_price": current_price,
                "market_cap": info.get("marketCap"),
                "pe_ratio": info.get("trailingPE") or info.get("forwardPE"),
                "pb_ratio": info.get("priceToBook"),
                "roe": roe_raw,
                "dividend_yield": dy_raw,
                "payout_ratio": payout_raw,
                "net_debt": net_debt,
                "ebitda": ebitda,
                "total_debt": total_debt,
                "total_cash": total_cash,
                "net_debt_ebitda": net_debt_ebitda,
                "shares_outstanding": info.get("sharesOutstanding"),
                "currency": info.get("currency", "BRL"),
                "exchange": info.get("exchange", "SAO"),
            }
    except Exception as e:
        logger.error(f"Erro ao buscar fundamentais para {ticker_sa}: {e}")

    # ── Preço atual: fallback para último fechamento ─────────────────────────
    if fundamentals.get("current_price") is None and df is not None and not df.empty:
        fundamentals["current_price"] = float(df["Close"].iloc[-1])

    # ── Corrige DY com cálculo próprio (Trailing 12 Months) ──────────────────
    current_price = fundamentals.get("current_price")
    if dividends is not None and not dividends.empty and current_price and current_price > 0:
        trailing_cutoff = pd.Timestamp.now() - pd.Timedelta(days=365)
        trailing_divs = dividends[dividends.index >= trailing_cutoff]
        if not trailing_divs.empty:
            t12m_yield = float(trailing_divs.sum()) / float(current_price)
            fundamentals["dividend_yield"] = t12m_yield
            logger.info(
                f"DY corrigido (T12M): {t12m_yield*100:.2f}% "
                f"(era: {fundamentals.get('dividend_yield_raw', 'N/D')})"
            )

    return df, dividends, fundamentals
