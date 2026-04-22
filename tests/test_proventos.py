"""
Testes que TRANCAM a regra tributaria do Simulador/Meta de Renda:
  - IR de 15% incide APENAS sobre JCP e rendimentos tributados.
  - Dividendos sao ISENTOS de IR para PF (sempre).
  - FIIs sao ISENTOS para PF (Lei 11.033/2004).
  - Expressao "15% sobre total" e PROIBIDA em qualquer rotulo do app.

Roda com: pytest tests/test_proventos.py
"""

import sys
import os
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from data.provider import get_proventos_summary


def _mock_si_records(div: float = 0.0, jcp: float = 0.0, rend: float = 0.0):
    """Constroi registros no formato interno do _parse_status_invest_records."""
    base_date = pd.Timestamp.now().tz_localize(None) - pd.DateOffset(months=6)
    out = []
    if div > 0:
        out.append({"data": base_date, "tipo": "DIVIDENDO", "valor": div})
    if jcp > 0:
        out.append({"data": base_date, "tipo": "JCP", "valor": jcp})
    if rend > 0:
        out.append({"data": base_date, "tipo": "RENDIMENTO", "valor": rend})
    return out


def test_dividendo_puro_nao_sofre_ir():
    """Acao so com dividendo: liquido == bruto, rotulo 'Isento' (nao 'JCP')."""
    with patch("data.provider._fetch_proventos_status_invest",
               return_value=_mock_si_records(div=1.00)):
        r = get_proventos_summary("TEST3", 12, discount_jcp=True, is_fii=False)
    assert r["source"] == "status_invest"
    assert abs(r["total_12m"] - 1.00) < 1e-6
    assert abs(r["liquido_12m"] - 1.00) < 1e-6, "dividendo isento — liquido = bruto"
    assert r["ir_label"] == "Isento", f"esperado 'Isento', obtido {r['ir_label']!r}"


def test_jcp_puro_tem_ir_15():
    """Acao so com JCP: liquido = bruto * 0.85, rotulo '15% sobre JCP'."""
    with patch("data.provider._fetch_proventos_status_invest",
               return_value=_mock_si_records(jcp=1.00)):
        r = get_proventos_summary("TEST3", 12, discount_jcp=True, is_fii=False)
    assert abs(r["liquido_12m"] - 0.85) < 1e-6
    assert r["ir_label"] == "15% sobre JCP"


def test_dividendo_mais_jcp_ir_somente_no_jcp():
    """0.50 div (isento) + 0.50 JCP (15% IR) -> liquido = 0.50 + 0.425 = 0.925.
    Jamais pode ser 0.85 (que seria 15% sobre o total, proibido)."""
    with patch("data.provider._fetch_proventos_status_invest",
               return_value=_mock_si_records(div=0.50, jcp=0.50)):
        r = get_proventos_summary("TEST3", 12, discount_jcp=True, is_fii=False)
    assert abs(r["liquido_12m"] - 0.925) < 1e-6, \
        f"liquido esperado 0.925 (0.50 + 0.425), obtido {r['liquido_12m']}"
    assert r["liquido_12m"] != 0.85, "NUNCA pode aplicar 15% sobre o total"
    assert r["ir_label"] == "15% sobre JCP"


def test_fii_sempre_isento():
    """FII: liquido = bruto, rotulo 'Isento', independe do discount_jcp."""
    with patch("data.provider._fetch_proventos_yfinance",
               return_value=[{"data": pd.Timestamp.now().tz_localize(None),
                              "tipo": "MISTO", "valor": 1.00}]):
        r = get_proventos_summary("MXRF11", 12, discount_jcp=True, is_fii=True)
    assert abs(r["liquido_12m"] - 1.00) < 1e-6
    assert r["ir_label"] == "Isento"


def test_fallback_yfinance_nao_usa_15_sobre_total():
    """Quando Status Invest falha, fallback usa heuristica setorial.
    BBAS3 (banco) -> fator 0.865; ticker generico -> fator 0.925.
    Jamais aplicar 15% cego sobre o total (fator 0.85)."""
    with patch("data.provider._fetch_proventos_status_invest",
               side_effect=RuntimeError("simulated downtime")), \
         patch("data.provider._fetch_proventos_yfinance",
               return_value=[{"data": pd.Timestamp.now().tz_localize(None),
                              "tipo": "MISTO", "valor": 1.00}]):
        r_bank = get_proventos_summary("BBAS3", 12, discount_jcp=True, is_fii=False)
        r_any = get_proventos_summary("PETR4", 12, discount_jcp=True, is_fii=False)
    assert r_bank["source"] == "yfinance_fallback"
    assert abs(r_bank["liquido_12m"] - 0.865) < 1e-6, "banco -> fator 0.865"
    assert abs(r_any["liquido_12m"] - 0.925) < 1e-6, "generico -> fator 0.925"
    assert r_bank["liquido_12m"] != 0.85, "fallback NUNCA usa fator 0.85"
    assert r_bank["ir_label"] == "15% sobre JCP (estimado)"
    assert r_any["ir_label"] == "15% sobre JCP (estimado)"


def test_ir_label_nunca_contem_sobre_total():
    """Todos os cenarios produzidos por get_proventos_summary devem NUNCA
    incluir a frase 'sobre total' no rotulo de IR."""
    cenarios = [
        ("TEST3", False, _mock_si_records(div=1.00)),
        ("TEST3", False, _mock_si_records(jcp=1.00)),
        ("TEST3", False, _mock_si_records(div=0.5, jcp=0.5)),
        ("MXRF11", True, [{"data": pd.Timestamp.now().tz_localize(None),
                           "tipo": "MISTO", "valor": 1.00}]),
    ]
    for ticker, is_fii, records in cenarios:
        patch_target = ("data.provider._fetch_proventos_yfinance" if is_fii
                        else "data.provider._fetch_proventos_status_invest")
        with patch(patch_target, return_value=records):
            for discount in (True, False):
                r = get_proventos_summary(ticker, 12, discount_jcp=discount, is_fii=is_fii)
                assert "sobre total" not in r["ir_label"].lower(), \
                    f"cenario {ticker}/{is_fii}/{discount} produziu rotulo proibido: {r['ir_label']!r}"


def test_toggle_ir_off_sempre_bruto():
    """Com discount_jcp=False, nenhum desconto e aplicado e rotulo e 'Bruto'."""
    with patch("data.provider._fetch_proventos_status_invest",
               return_value=_mock_si_records(div=0.5, jcp=0.5)):
        r = get_proventos_summary("TEST3", 12, discount_jcp=False, is_fii=False)
    assert abs(r["liquido_12m"] - 1.00) < 1e-6
    assert r["ir_label"] == "Bruto (sem IR)"


if __name__ == "__main__":
    # Roda sem pytest: execucao direta
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
