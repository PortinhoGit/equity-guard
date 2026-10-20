"""
update_prevdow_file.py — Equity Guard

Atualiza data/prevdow_latest.json com a rentabilidade mais recente do portal
PrevDow. Projetado para rodar no GitHub Actions (dia ~15-20 de cada mes):

    scraper (Playwright, fura o Akamai)  ->  grava o JSON  ->  o workflow
    commita/empurra  ->  o Streamlit Cloud redeploya  ->  app mostra o novo mes.

Idempotente: se o mes do portal ja esta no arquivo, nao altera nada (o workflow
so commita quando ha diff). NAO depende de Supabase — essa e justamente a
razao de existir: o PrevDow passa a atualizar sozinho, sem o banco (que no
plano free pausa por inatividade e travava a automacao).

Saida: exit code 0 sempre que o fluxo roda sem erro (com ou sem mudanca);
       imprime "CHANGED" na ultima linha quando o arquivo foi atualizado.
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

OUT = Path(__file__).parent / "data" / "prevdow_latest.json"


def main() -> int:
    from data.prevdow_scraper import get_rentabilidade_prevdow

    data = get_rentabilidade_prevdow()
    if not data or not data.get("data_base"):
        print("Scraper retornou vazio — portal indisponivel ou bloqueou. Nada a fazer.")
        return 0

    if data.get("cdi_month") is None and data.get("balanced_month") is None:
        print("Scraper sem valores de rentabilidade. Nada a fazer.")
        return 0

    existing = {}
    if OUT.exists():
        try:
            existing = json.loads(OUT.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            existing = {}

    if existing.get("data_base") == data["data_base"]:
        print(f"{data['data_base']} ja esta em {OUT.name}. Nada a fazer.")
        return 0

    row = {
        "data_base":      data["data_base"],
        "cdi_month":      data.get("cdi_month"),
        "balanced_month": data.get("balanced_month"),
        "cdi_year":       data.get("cdi_year"),
        "balanced_year":  data.get("balanced_year"),
        "inserted_at":    datetime.utcnow().isoformat() + "Z",
    }
    OUT.write_text(json.dumps(row, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Atualizado {OUT.name}: {row}")
    print("CHANGED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
