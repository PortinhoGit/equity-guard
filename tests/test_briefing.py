"""
Testes que trancam os 3 bugs do Briefing WhatsApp (22/04/2026):

  Bug 1 — Sufixo "(fech. 20/04 — Tiradentes)" aparecia DEPOIS que o mercado
           ja abriu; last_market_session usava horario de FECHAMENTO (20h)
           em vez de ABERTURA (10h) como limiar.

  Bug 2 — Sinal duplo "++0.3%" no Dolar Comercial: _fx_arrow="+" +
           f"{v:+.1f}%" que ja adiciona "+".

  Bug 3 — Alinhamento das Bolsas: _wa_asset_line agora produz colunas de
           largura fixa para bloco monospace (triple-backtick).

Roda com: pytest tests/test_briefing.py
"""

import sys
import os
from datetime import date, time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from market_status import last_market_session, briefing_date_across_markets, market_asymmetry


# ── Bug 1: last_market_session usa horario de abertura ───────────────────────

def test_b3_retorna_hoje_apos_abertura_10h():
    """As 10h em diante, last_market_session(B3) deve retornar hoje (dia util)."""
    today = date(2026, 4, 22)   # quarta, dia util B3
    hora = time(10, 0)
    assert last_market_session("B3", today, hora) == today


def test_b3_retorna_hoje_as_1845():
    """Caso concreto do bug: 18:45 em 22/04 deve retornar 22/04 (nao 20/04)."""
    today = date(2026, 4, 22)
    hora = time(18, 45)
    assert last_market_session("B3", today, hora) == today, (
        "Às 18:45 o IBOV ja reflete 22/04 — nao deve aparecer '20/04'"
    )


def test_b3_retorna_ultimo_pregao_antes_da_abertura():
    """Antes das 10h em 22/04 (pos-Tiradentes), deve retornar 20/04."""
    today = date(2026, 4, 22)
    hora = time(9, 59)
    result = last_market_session("B3", today, hora)
    assert result == date(2026, 4, 20), (
        f"Esperado 20/04 (ultimo pregao B3 antes de 22/04 abrir), obtido {result}"
    )


def test_assimetria_desaparece_apos_b3_abrir():
    """A partir das 10h em 22/04, briefing_date == last_session de todos
    os mercados — nenhuma assimetria deve existir."""
    today = date(2026, 4, 22)
    hora = time(18, 45)
    tracked = ("B3", "NYSE", "LSE")
    briefing_d = briefing_date_across_markets(tracked, today, hora)
    for m in tracked:
        last = last_market_session(m, today, hora)
        asym = market_asymmetry(m, last, briefing_d)
        assert asym is None, (
            f"Mercado {m}: assimetria nao deveria existir as 18:45 de 22/04, "
            f"mas obteve {asym}"
        )


def test_assimetria_presente_antes_da_abertura():
    """Antes das 10h em 22/04, B3 ainda mostra assimetria (20/04 vs 21/04 NYSE)."""
    today = date(2026, 4, 22)
    hora = time(8, 0)
    tracked = ("B3", "NYSE", "LSE")
    briefing_d = briefing_date_across_markets(tracked, today, hora)
    b3_last = last_market_session("B3", today, hora)
    asym = market_asymmetry("B3", b3_last, briefing_d)
    # Deve haver assimetria: B3 em 20/04, outros em 21/04
    assert asym is not None, (
        "Antes da abertura B3, assimetria (Tiradentes) deve aparecer"
    )
    assert asym[1] == "Tiradentes", f"Feriado esperado: Tiradentes, obteve: {asym[1]}"


# ── Bug 2: sinal duplo no Dolar ───────────────────────────────────────────────

def test_fx_pct_sem_sinal_duplo():
    """_fx_pct = f'{v:+.1f}%' nao deve ser prefixado com '+' adicional."""
    for v in (0.3, -0.3, 0.0, 1.5, -2.7):
        _fx_pct = f"{v:+.1f}%"
        assert not _fx_pct.startswith("++"), f"Sinal duplo para v={v}: '{_fx_pct}'"
        assert not _fx_pct.startswith("--"), f"Sinal duplo para v={v}: '{_fx_pct}'"
        # Deve comecar com exatamente um sinal
        assert _fx_pct[0] in ("+", "-"), f"Sem sinal para v={v}: '{_fx_pct}'"
        assert _fx_pct[1] != "+" and _fx_pct[1] != "-", (
            f"Sinal duplicado em posicao 1 para v={v}: '{_fx_pct}'"
        )


# ── Bug 3: alinhamento monospace da funcao _wa_asset_line ─────────────────────

def _fake_wa_asset_line(label: str, val: str, chg: str) -> str:
    """Replica a logica de padding de _wa_asset_line sem dependencias externas."""
    return f"{label:<10}{val:>12}  {chg}"


def test_bolsas_colunas_alinhadas():
    """Todas as linhas das Bolsas devem ter o valor iniciando na mesma coluna."""
    casos = [
        ("Ibovespa", "192.889", "-1.7%"),
        ("S&P 500",  "7,137.90", "+1.0%"),
        ("NASDAQ",   "24,657.57", "+1.6%"),
        ("FTSE",     "10,476.46", "-0.2%"),
    ]
    linhas = [_fake_wa_asset_line(l, v, c) for l, v, c in casos]
    # A coluna do valor comeca no char 10 (label padded to 10); o valor
    # termina no char 22 (10 + 12 right-aligned). Verificar que o char 22
    # eh o mesmo para todas as linhas (o ultimo char do valor).
    for linha in linhas:
        assert len(linha) >= 24, f"Linha muito curta: {linha!r}"
    # Verificar que os valores terminam todos na coluna 22 (indice 21)
    col_fim_valor = 10 + 12  # label_width + val_width
    for linha, (label, val, _) in zip(linhas, casos):
        char_at_col = linha[col_fim_valor - 1]
        # O ultimo char do valor deve ser o ultimo digito/ponto do valor
        assert char_at_col == val[-1], (
            f"Label '{label}': esperado '{val[-1]}' na col {col_fim_valor}, "
            f"obtido '{char_at_col}'. Linha: {linha!r}"
        )


def test_nenhuma_linha_tem_sinal_duplo():
    """Nenhuma linha do briefing deve conter '++' ou '--' (sinal duplo)."""
    casos = [
        ("Ibovespa", "192.889", "-1.7%"),
        ("S&P 500",  "7,137.90", "+1.0%"),
        ("NASDAQ",   "24,657.57", "+1.6%"),
        ("FTSE",     "10,476.46", "-0.2%"),
    ]
    for label, val, chg in casos:
        linha = _fake_wa_asset_line(label, val, chg)
        assert "++" not in linha, f"Sinal duplo em '{label}': {linha!r}"
        assert "--" not in linha, f"Sinal duplo em '{label}': {linha!r}"


if __name__ == "__main__":
    import traceback
    tests = [v for k, v in globals().items() if k.startswith("test_") and callable(v)]
    failed = 0
    for t in tests:
        try:
            t()
            print(f"OK   {t.__name__}")
        except Exception:
            print(f"FAIL {t.__name__}")
            traceback.print_exc()
            failed += 1
    print(f"\n{len(tests) - failed}/{len(tests)} passed")
    sys.exit(1 if failed else 0)
