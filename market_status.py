"""
market_status.py — Equity Guard
Determina se o mercado está aberto ou fechado e qual a data de referência.
"""

from datetime import date, time, datetime, timedelta
from typing import Dict

# Feriados B3 2026 (dias sem pregão, além de fins de semana)
FERIADOS_B3_2026 = {
    date(2026, 1, 1),   # Confraternização Universal
    date(2026, 2, 16),  # Carnaval
    date(2026, 2, 17),  # Carnaval
    date(2026, 2, 18),  # Quarta de Cinzas (até 13h, mas simplificamos)
    date(2026, 4, 3),   # Sexta-feira Santa
    date(2026, 4, 21),  # Tiradentes
    date(2026, 5, 1),   # Dia do Trabalho
    date(2026, 6, 4),   # Corpus Christi
    date(2026, 9, 7),   # Independência
    date(2026, 10, 12), # N. S. Aparecida
    date(2026, 11, 2),  # Finados
    date(2026, 11, 15), # Proclamação da República
    date(2026, 11, 20), # Consciência Negra
    date(2026, 12, 24), # Véspera de Natal (B3 fechada)
    date(2026, 12, 25), # Natal
    date(2026, 12, 31), # Véspera de Ano Novo (B3 fechada)
}


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
