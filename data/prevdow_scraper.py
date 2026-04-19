"""
data/prevdow_scraper.py — Equity Guard
Scraper do portal PrevDow que extrai rentabilidade da variável JS seriesOriginal.
"""

import re
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)

PREVDOW_URL = "https://www.portalprev.com.br/Prevdow/prevdow/Site/Public/Rentabilidade/"
HOME_URL = "https://www.portalprev.com.br/"

_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)


def get_rentabilidade_prevdow() -> Optional[Dict]:
    """
    Extrai rentabilidade (último mês) do portal PrevDow.
    Retorna dict com data_base, cdi_month, balanced_month, ou None em falha.
    """
    try:
        import requests
    except ImportError:
        logger.warning("requests nao instalado")
        return None

    try:
        session = requests.Session()
        # Aquece sessao na home para obter cookies
        session.get(HOME_URL, headers={
            "User-Agent": _UA,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        }, timeout=15)

        headers = {
            "User-Agent": _UA,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
            "Accept-Encoding": "gzip, deflate, br",
            "Referer": HOME_URL,
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Cache-Control": "max-age=0",
        }
        r = session.get(PREVDOW_URL, headers=headers, timeout=20)
        r.raise_for_status()
        html = r.text
    except Exception as e:
        logger.warning(f"Falha ao buscar PrevDow: {e}")
        return None

    match = re.search(
        r"var\s+seriesOriginal\s*=\s*(\[[\s\S]*?\]);\s*var\s+categoriasOriginal",
        html,
    )
    if not match:
        logger.warning("seriesOriginal nao encontrada no HTML")
        return None
    series_raw = match.group(1)

    def _extrair(nome: str) -> Optional[float]:
        pattern = rf'name:\s*"{re.escape(nome)}"[\s\S]*?data:\s*\[([\d\s,.\-]+)\]'
        m = re.search(pattern, series_raw)
        if m:
            valores = [float(v.strip()) for v in m.group(1).split(",") if v.strip()]
            return valores[0] if valores else None
        return None

    cdi_month = _extrair("Carteira DI")
    balanced_month = _extrair("Carteira Original Balanceada")

    db_match = re.search(r"Data Base:\s*([\d/]+)", html)
    data_base = db_match.group(1) if db_match else None

    if cdi_month is None and balanced_month is None:
        logger.warning("Nenhum valor extraido do PrevDow")
        return None

    result = {
        "data_base": data_base,
        "cdi_month": cdi_month,
        "balanced_month": balanced_month,
    }
    logger.info(f"PrevDow scraper: {result}")
    return result


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print(get_rentabilidade_prevdow())
