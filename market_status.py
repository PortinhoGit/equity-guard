"""
market_status.py — Equity Guard
Determina se o mercado está aberto ou fechado e qual a data de referência.
Suporta calendarios B3, NYSE e LSE para tratar assimetria de feriados.
"""

from datetime import date, time, datetime, timedelta
from typing import Dict, Optional, Tuple, Iterable

# ── B3 (BOVESPA) 2026 ────────────────────────────────────────────────────────
FERIADOS_B3_2026_NAMED: Dict[date, str] = {
    date(2026, 1, 1):   "Confraternização Universal",
    date(2026, 2, 16):  "Carnaval",
    date(2026, 2, 17):  "Carnaval",
    date(2026, 2, 18):  "Quarta de Cinzas",
    date(2026, 4, 3):   "Sexta-feira Santa",
    date(2026, 4, 21):  "Tiradentes",
    date(2026, 5, 1):   "Dia do Trabalho",
    date(2026, 6, 4):   "Corpus Christi",
    date(2026, 9, 7):   "Independência",
    date(2026, 10, 12): "N. S. Aparecida",
    date(2026, 11, 2):  "Finados",
    date(2026, 11, 15): "Proclamação da República",
    date(2026, 11, 20): "Consciência Negra",
    date(2026, 12, 24): "Véspera de Natal",
    date(2026, 12, 25): "Natal",
    date(2026, 12, 31): "Véspera de Ano Novo",
}
FERIADOS_B3_2026 = set(FERIADOS_B3_2026_NAMED.keys())

# ── NYSE 2026 (NYSE holiday calendar oficial) ────────────────────────────────
FERIADOS_NYSE_2026_NAMED: Dict[date, str] = {
    date(2026, 1, 1):   "New Year's Day",
    date(2026, 1, 19):  "Martin Luther King Jr. Day",
    date(2026, 2, 16):  "Presidents' Day",
    date(2026, 4, 3):   "Good Friday",
    date(2026, 5, 25):  "Memorial Day",
    date(2026, 6, 19):  "Juneteenth",
    date(2026, 7, 3):   "Independence Day (observado)",
    date(2026, 9, 7):   "Labor Day",
    date(2026, 11, 26): "Thanksgiving",
    date(2026, 12, 25): "Christmas Day",
}

# ── LSE 2026 (UK bank holidays) ──────────────────────────────────────────────
FERIADOS_LSE_2026_NAMED: Dict[date, str] = {
    date(2026, 1, 1):   "New Year's Day",
    date(2026, 4, 3):   "Good Friday",
    date(2026, 4, 6):   "Easter Monday",
    date(2026, 5, 4):   "Early May Bank Holiday",
    date(2026, 5, 25):  "Spring Bank Holiday",
    date(2026, 8, 31):  "Summer Bank Holiday",
    date(2026, 12, 25): "Christmas Day",
    date(2026, 12, 28): "Boxing Day (observado)",
}

_MARKET_HOLIDAYS: Dict[str, Dict[date, str]] = {
    "B3":   FERIADOS_B3_2026_NAMED,
    "NYSE": FERIADOS_NYSE_2026_NAMED,
    "LSE":  FERIADOS_LSE_2026_NAMED,
}

# Horario de fechamento (em Brasilia) — usado pra decidir se o pregao de "hoje"
# ja terminou. Valores conservadores:
#   B3:   20h (inclui after-market)
#   NYSE: 18h (regular close 17h EST / 16h EDT + margem)
#   LSE:  14h (16:30 Londres = 13:30-14:30 BRT conforme DST)
_MARKET_CLOSE_BRT: Dict[str, time] = {
    "B3":   time(20, 0),
    "NYSE": time(18, 0),
    "LSE":  time(14, 0),
}

_MARKET_FLAG = {"B3": "🇧🇷", "NYSE": "🇺🇸", "LSE": "🇬🇧"}
_MARKET_LABEL_PT = {"B3": "B3", "NYSE": "NYSE", "LSE": "LSE"}


def market_flag(market: str) -> str:
    return _MARKET_FLAG.get(market, "")


def is_market_session(market: str, d: date) -> bool:
    """True se o mercado opera no dia d (nao e fim de semana nem feriado)."""
    if d.weekday() >= 5:
        return False
    return d not in _MARKET_HOLIDAYS.get(market, {})


def last_market_session(market: str, today: date, hora_brt: time) -> date:
    """Ultima data com pregao efetivamente encerrado dessa bolsa.
    Se hoje e dia util e o pregao ja fechou (hora_brt >= horario de corte do
    mercado), retorna hoje; senao volta ate achar um dia util anterior."""
    close_h = _MARKET_CLOSE_BRT.get(market, time(20, 0))
    d = today
    if is_market_session(market, d) and hora_brt >= close_h:
        return d
    d -= timedelta(days=1)
    while not is_market_session(market, d):
        d -= timedelta(days=1)
    return d


def briefing_date_across_markets(markets: Iterable[str], today: date, hora_brt: time) -> date:
    """Data de referencia do briefing = max(last_session) entre os mercados
    rastreados. Reflete a ultima sessao GLOBAL encerrada — evita que um
    feriado isolado em um mercado atrase o rotulo do briefing inteiro."""
    return max(last_market_session(m, today, hora_brt) for m in markets)


def market_asymmetry(market: str, last_session: date, briefing_date: date) -> Optional[Tuple[date, str]]:
    """Se o last_session desse mercado e anterior ao briefing_date, busca o
    feriado do proprio mercado dentro da janela (last_session, briefing_date]
    que explica o atraso. Retorna (data_feriado, nome) ou None se nao houver
    assimetria relevante."""
    if last_session >= briefing_date:
        return None
    d = briefing_date
    holidays = _MARKET_HOLIDAYS.get(market, {})
    while d > last_session:
        name = holidays.get(d)
        if name:
            return (d, name)
        d -= timedelta(days=1)
    return None


def is_dst_eua(d: date) -> bool:
    """
    Horário de verão nos EUA: 2o domingo de março até 1o domingo de novembro.
    Durante o DST, NYSE fecha às 17h Brasília (em vez de 18h).
    """
    year = d.year
    # 2o domingo de março
    mar1 = date(year, 3, 1)
    first_sun_mar = mar1 + timedelta(days=(6 - mar1.weekday()) % 7)
    dst_start = first_sun_mar + timedelta(weeks=1)
    # 1o domingo de novembro
    nov1 = date(year, 11, 1)
    dst_end = nov1 + timedelta(days=(6 - nov1.weekday()) % 7)
    return dst_start <= d < dst_end


def is_dia_util(d: date) -> bool:
    """Verifica se é dia útil (não é fim de semana nem feriado B3)."""
    if d.weekday() >= 5:
        return False
    if d in FERIADOS_B3_2026:
        return False
    return True


def ultimo_dia_util(d: date) -> date:
    """Retorna o último dia útil igual ou anterior a d."""
    while not is_dia_util(d):
        d -= timedelta(days=1)
    return d


def dia_util_anterior(d: date) -> date:
    """Retorna o dia útil anterior a d (não inclui d)."""
    d -= timedelta(days=1)
    return ultimo_dia_util(d)


HORA_CORTE = time(20, 0)
HORA_ABERTURA = time(10, 0)


def get_status_mercado() -> Dict:
    """
    Retorna o estado atual do mercado.
    Corte fixo: 20h Brasília (último mercado a fechar = Brent/WTI ~20h).
    Abertura: 10h Brasília (B3).

    Returns:
        {
            "estado": "ONLINE" | "FECHAMENTO",
            "data_ref": date do último pregão,
            "data_anterior": date do pregão anterior ao data_ref,
            "hora_corte": time(20, 0),
            "label": str para exibição,
        }
    """
    import pytz
    brt = pytz.timezone("America/Sao_Paulo")
    now = datetime.now(brt)
    hoje = now.date()
    hora_atual = now.time()

    if is_dia_util(hoje) and HORA_ABERTURA <= hora_atual < HORA_CORTE:
        data_ref = hoje
        data_ant = dia_util_anterior(hoje)
        return {
            "estado": "ONLINE",
            "data_ref": data_ref,
            "data_anterior": data_ant,
            "hora_corte": HORA_CORTE,
            "label": f"Online {now.strftime('%d/%m/%Y %H:%M:%S')} (Brasilia)",
        }
    else:
        if is_dia_util(hoje) and hora_atual >= HORA_CORTE:
            # Dia util apos o corte (pos-20h): fechamento e de hoje.
            data_ref = hoje
        elif is_dia_util(hoje) and hora_atual < HORA_ABERTURA:
            # Dia util antes da abertura (pre-10h): fechamento ainda e do
            # ultimo dia util anterior. Sem isso, o app mostrava FECHAMENTO
            # do dia corrente as 6h da manha.
            data_ref = dia_util_anterior(hoje)
        else:
            # Fim de semana, feriado, ou estado indefinido.
            data_ref = ultimo_dia_util(hoje)
        data_ant = dia_util_anterior(data_ref)
        return {
            "estado": "FECHAMENTO",
            "data_ref": data_ref,
            "data_anterior": data_ant,
            "hora_corte": HORA_CORTE,
            "label": f"Fechamento {data_ref.strftime('%d/%m/%Y')}",
        }
