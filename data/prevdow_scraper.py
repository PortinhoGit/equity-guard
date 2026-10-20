"""
data/prevdow_scraper.py — Equity Guard
Scraper do portal PrevDow que extrai rentabilidade da variável JS seriesOriginal.

O portal fica atrás do Akamai Bot Manager, que responde 403 a requisição "crua"
de servidor (GitHub Actions, Streamlit Cloud etc.). Estratégia em dois passos:

  1) requests  — rápido; funciona onde o Akamai não barra.
  2) navegador headless (Playwright/Chromium) — executa o JS do Akamai, obtém o
     cookie e passa o 403. Só é usado se o Playwright estiver instalado (no job
     do GitHub Actions). Em ambientes sem navegador (Streamlit Cloud) o passo 2
     é pulado e a função retorna None — o app então usa o Supabase como fonte.
"""

import os
import re
import time
import logging
from typing import Dict, Optional, List

logger = logging.getLogger(__name__)

PREVDOW_URL = "https://www.portalprev.com.br/Prevdow/prevdow/Site/Public/Rentabilidade/"
HOME_URL = "https://www.portalprev.com.br/"

_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)


# ── Passo 1: requests ────────────────────────────────────────────────────────
def _fetch_via_requests() -> Optional[str]:
    try:
        import requests
    except ImportError:
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
        return r.text
    except Exception as e:
        logger.info(f"requests falhou ({e}); tentando navegador headless...")
        return None


# ── Passo 2: navegador headless (Playwright) ─────────────────────────────────
def _fetch_via_browser() -> Optional[str]:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        logger.info("Playwright nao instalado; pulando fallback de navegador.")
        return None
    # Permite apontar um Chromium especifico (ambientes com versao divergente).
    exe = os.environ.get("PLAYWRIGHT_EXECUTABLE_PATH") or None
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                executable_path=exe,
                args=["--no-sandbox", "--disable-dev-shm-usage"],
            )
            try:
                ctx = browser.new_context(user_agent=_UA, locale="pt-BR")
                page = ctx.new_page()
                page.goto(PREVDOW_URL, wait_until="domcontentloaded", timeout=60000)
                # O Akamai/JS injeta o conteudo; espera a variavel aparecer.
                html = page.content()
                for _ in range(20):
                    if "seriesOriginal" in html and "categoriasOriginal" in html:
                        break
                    time.sleep(0.5)
                    html = page.content()
                return html
            finally:
                browser.close()
    except Exception as e:
        logger.warning(f"Navegador headless falhou: {e}")
        return None


# ── Parsing ──────────────────────────────────────────────────────────────────
def _parse(html: str) -> Optional[Dict]:
    # ; opcional: o portal ora emite "}];" ora "}]" antes de categoriasOriginal.
    match = re.search(
        r"var\s+seriesOriginal\s*=\s*(\[[\s\S]*?\])\s*;?\s*var\s+categoriasOriginal",
        html,
    )
    if not match:
        logger.warning("seriesOriginal nao encontrada no HTML")
        return None
    series_raw = match.group(1)

    def _extrair(nome: str) -> Optional[List[float]]:
        """Lista 'data' do indice: [1mes, 6m, 12m, 24m, 36m, Ano]."""
        pattern = rf'name:\s*"{re.escape(nome)}"[\s\S]*?data:\s*\[([\d\s,.\-]+)\]'
        m = re.search(pattern, series_raw)
        if m:
            valores = [float(v.strip()) for v in m.group(1).split(",") if v.strip()]
            return valores or None
        return None

    cdi = _extrair("Carteira DI")
    balanced = _extrair("Carteira Original Balanceada")

    # Posicao 0 = mes; ultima posicao = "Ano" (ver categoriasOriginal no portal).
    cdi_month = cdi[0] if cdi else None
    balanced_month = balanced[0] if balanced else None
    cdi_year = cdi[-1] if cdi and len(cdi) >= 2 else None
    balanced_year = balanced[-1] if balanced and len(balanced) >= 2 else None

    db_match = re.search(r"Data Base:\s*([\d/]+)", html)
    data_base = db_match.group(1) if db_match else None

    if cdi_month is None and balanced_month is None:
        logger.warning("Nenhum valor extraido do PrevDow")
        return None

    result = {
        "data_base": data_base,
        "cdi_month": cdi_month,
        "balanced_month": balanced_month,
        "cdi_year": cdi_year,
        "balanced_year": balanced_year,
    }
    logger.info(f"PrevDow scraper: {result}")
    return result


def get_rentabilidade_prevdow() -> Optional[Dict]:
    """
    Extrai rentabilidade (último mês) do portal PrevDow.
    Retorna dict com data_base, cdi_month, balanced_month, cdi_year,
    balanced_year — ou None em falha.
    """
    html = _fetch_via_requests()
    if not html or "seriesOriginal" not in html:
        html = _fetch_via_browser()
    if not html:
        return None
    return _parse(html)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print(get_rentabilidade_prevdow())
