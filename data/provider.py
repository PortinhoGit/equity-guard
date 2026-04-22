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
    Busca fechamento + variação dia/YTD/1ano dos principais índices e commodities.
    Retorna lista de dicts com: name, symbol, locale, last, change, chg_ytd, chg_1y.
    """
    results = []
    for name, sym, locale in _GLOBAL_TICKERS:
        entry = {"name": name, "symbol": sym, "locale": locale,
                 "last": None, "change": None, "chg_ytd": None, "chg_1y": None}
        try:
            tk = yf.Ticker(sym)
            hist = tk.history(period="13mo", interval="1d", auto_adjust=True)
            if hist is None or hist.empty:
                results.append(entry)
                continue
            closes = hist["Close"].dropna()
            if closes.index.tz is not None:
                closes.index = closes.index.tz_localize(None)
            if len(closes) < 2:
                results.append(entry)
                continue
            last = float(closes.iloc[-1])
            prev = float(closes.iloc[-2])
            entry["last"] = last
            entry["change"] = ((last - prev) / prev * 100) if prev else 0.0
            jan1 = pd.Timestamp(pd.Timestamp.now().year, 1, 1)
            ytd_data = closes[closes.index <= jan1 + pd.Timedelta(days=5)]
            if not ytd_data.empty:
                ytd_price = float(ytd_data.iloc[-1])
                entry["chg_ytd"] = ((last - ytd_price) / ytd_price * 100) if ytd_price else None
            y1_cutoff = pd.Timestamp.now() - pd.Timedelta(days=365)
            y1_data = closes[closes.index <= y1_cutoff + pd.Timedelta(days=5)]
            if not y1_data.empty:
                y1_price = float(y1_data.iloc[-1])
                entry["chg_1y"] = ((last - y1_price) / y1_price * 100) if y1_price else None
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
    # ── yfinance (comercial) — fonte primaria live durante o pregao ─────────
    # fast_info.last_price e uma leitura intradiaria; history(1d) da o close
    # mais recente como backup. BCB PTAX e fallback apenas se yfinance falhar.
    try:
        tk = yf.Ticker("USDBRL=X")
        fi = getattr(tk, "fast_info", None)
        if fi is not None:
            for _k in ("last_price", "lastPrice"):
                try:
                    _v = fi.get(_k) if hasattr(fi, "get") else getattr(fi, _k, None)
                    if _v:
                        ask = float(_v)
                        break
                except Exception:
                    continue
        hist = tk.history(period="13mo", interval="1d", auto_adjust=True)
        if hist is None or hist.empty:
            if ask is None:
                # Ainda sem cotacao — tenta BCB PTAX ultimo boletim como fallback
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
                    logger.warning(f"BCB PTAX fallback falhou: {e}")
            if ask is None:
                return None
            hist_ok = False
        else:
            hist_ok = True
    except Exception as e:
        logger.error(f"Erro ao buscar USDBRL=X: {e}")
        if ask is None:
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

    all_closes = hist["Close"].dropna() if hist_ok else None
    if all_closes is not None and all_closes.index.tz is not None:
        all_closes.index = all_closes.index.tz_localize(None)

    prev = float(series.iloc[-2]) if series is not None and len(series) >= 2 else ask
    chg = ((ask - prev) / prev * 100) if prev else 0.0

    chg_ytd = None
    chg_1y = None
    if all_closes is not None and len(all_closes) > 5:
        jan1 = pd.Timestamp(pd.Timestamp.now().year, 1, 1)
        ytd_data = all_closes[all_closes.index <= jan1 + pd.Timedelta(days=5)]
        if not ytd_data.empty:
            ytd_price = float(ytd_data.iloc[-1])
            chg_ytd = ((ask - ytd_price) / ytd_price * 100) if ytd_price else None
        y1_cutoff = pd.Timestamp.now() - pd.Timedelta(days=365)
        y1_data = all_closes[all_closes.index <= y1_cutoff + pd.Timedelta(days=5)]
        if not y1_data.empty:
            y1_price = float(y1_data.iloc[-1])
            chg_1y = ((ask - y1_price) / y1_price * 100) if y1_price else None

    TURISMO_SPREAD = 0.04
    tur_bid = round(bid * (1 + TURISMO_SPREAD), 4)
    tur_ask = round(ask * (1 + TURISMO_SPREAD), 4)
    prev_tur = round(prev * (1 + TURISMO_SPREAD), 4)

    # ── Yahoo market state + regularMarketTime (best-effort) ─────────────────
    # tk.info e pesado e sujeito a rate-limit; protegemos com try/except.
    # Fallback: usa timestamp do ultimo bar intraday (1m) se disponivel.
    market_state = ""
    market_time_ts: Optional[int] = None
    try:
        _info = getattr(tk, "info", None) or {}
        market_state = (_info.get("marketState") or "").upper()
        _rmt = _info.get("regularMarketTime")
        if _rmt:
            market_time_ts = int(_rmt)
    except Exception:
        pass
    if market_time_ts is None:
        try:
            _intra = tk.history(period="1d", interval="1m")
            if _intra is not None and not _intra.empty:
                _last_idx = _intra.index[-1]
                if hasattr(_last_idx, "timestamp"):
                    market_time_ts = int(_last_idx.timestamp())
        except Exception:
            pass

    return {
        "com_bid": bid, "com_ask": ask, "com_prev": prev,
        "tur_bid": tur_bid, "tur_ask": tur_ask, "tur_prev": prev_tur,
        "change": chg, "chg_ytd": chg_ytd, "chg_1y": chg_1y,
        "series": series,
        "last": ask, "prev": prev,
        "fetched_at": pd.Timestamp.now(tz="America/Sao_Paulo").tz_localize(None),
        "market_state": market_state,
        "market_time_ts": market_time_ts,
        "yf_ticker": "USDBRL=X",
    }


def get_ptax_bulletins(date_ref: Optional[str] = None) -> Dict[str, Any]:
    """
    Busca os boletins PTAX do BCB para uma data. Retorna:
      {
        "date": "YYYY-MM-DD",
        "bulletins": {
            10: {"bid": float, "ask": float, "ts": "HH:MM"},  # Intermediario 10h
            11: {...}, 12: {...}, 13: {...},
        },
        "closing": {"bid": float, "ask": float, "ts": "HH:MM"} | None,
        "source": "BCB Olinda PTAX",
      }
    `bulletins[h]` pode vir ausente quando a BC ainda nao publicou.
    date_ref: "MM-DD-YYYY" (formato BCB). None = hoje.
    """
    import requests as _req

    if date_ref is None:
        date_ref = pd.Timestamp.now(tz="America/Sao_Paulo").strftime("%m-%d-%Y")

    out: Dict[str, Any] = {
        "date": date_ref, "bulletins": {}, "closing": None,
        "source": "BCB Olinda PTAX",
    }

    try:
        # CotacaoMoedaDia expoe TODOS os boletins do dia (Abertura + 3
        # Intermediarios + Fechamento PTAX). CotacaoDolarDia so traz o
        # fechamento — nao serve pra esta secao.
        url = (
            "https://olinda.bcb.gov.br/olinda/servico/PTAX/versao/v1/odata/"
            "CotacaoMoedaDia(moeda=@m,dataCotacao=@d)"
            f"?@m='USD'&@d='{date_ref}'"
            "&$orderby=dataHoraCotacao%20asc&$format=json"
        )
        r = _req.get(url, timeout=6)
        if not r.ok:
            return out
        rows = r.json().get("value", []) or []
    except Exception as e:
        logger.warning(f"PTAX bulletins falhou: {e}")
        return out

    for row in rows:
        tipo = (row.get("tipoBoletim") or "").strip().lower()
        ts = row.get("dataHoraCotacao") or ""
        try:
            hh_mm = ts[11:16]     # "YYYY-MM-DD HH:MM:SS.sss"
            hour = int(ts[11:13])
        except (ValueError, IndexError):
            continue
        try:
            bid = float(row["cotacaoCompra"])
            ask = float(row["cotacaoVenda"])
        except (KeyError, TypeError, ValueError):
            continue
        payload = {"bid": bid, "ask": ask, "ts": hh_mm}
        if "fechamento" in tipo:
            out["closing"] = payload
        elif "intermediário" in tipo or "intermediario" in tipo:
            # BC publica boletins em HH:04-HH:05 para o slot HH. Usamos o hour
            # do timestamp como slot.
            if hour in (10, 11, 12, 13) and hour not in out["bulletins"]:
                out["bulletins"][hour] = payload
        elif "abertura" in tipo:
            # "Abertura" e equivalente ao slot 10h quando nao houver Intermediario.
            if 10 not in out["bulletins"]:
                out["bulletins"][10] = payload

    return out


def get_market_news(max_per_source: int = 3) -> list:
    """Busca manchetes de mercado do yfinance para Ibovespa e S&P 500."""
    results = []
    for label, sym in [("🇧🇷", "^BVSP"), ("🇺🇸", "^GSPC")]:
        try:
            news = yf.Ticker(sym).news or []
            for n in news[:max_per_source]:
                c = n.get("content", n)
                title = c.get("title", "")
                provider = c.get("provider", {})
                source = provider.get("displayName", "") if isinstance(provider, dict) else ""
                if title:
                    results.append({"flag": label, "title": title, "source": source})
        except Exception as e:
            logger.warning(f"News falhou para {sym}: {e}")
    return results


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
