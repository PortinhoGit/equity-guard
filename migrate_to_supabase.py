"""
migrate_to_supabase.py — Equity Guard
Script ONE-SHOT para copiar users_db.json local -> Supabase.

Uso (no diretorio do projeto):
    python3 migrate_to_supabase.py

Le SUPABASE_URL e SUPABASE_SERVICE_KEY de .streamlit/secrets.toml.
Idempotente: usa upsert para nao duplicar.
"""

import json
import re
import sys
from pathlib import Path


def _read_secret(key: str) -> str:
    secrets = Path(".streamlit/secrets.toml")
    if not secrets.exists():
        print("ERRO: .streamlit/secrets.toml nao encontrado.")
        sys.exit(1)
    m = re.search(rf'^{key}\s*=\s*"([^"]*)"', secrets.read_text(), re.MULTILINE)
    if not m:
        print(f"ERRO: {key} nao encontrado em secrets.toml")
        sys.exit(1)
    return m.group(1)


def main() -> None:
    db_path = Path("users_db.json")
    if not db_path.exists():
        print("Nenhum users_db.json local. Nada a migrar.")
        return

    data = json.loads(db_path.read_text())
    users = data.get("users", {})
    if not users:
        print("users_db.json esta vazio. Nada a migrar.")
        return

    from supabase import create_client
    client = create_client(_read_secret("SUPABASE_URL"), _read_secret("SUPABASE_SERVICE_KEY"))

    users_to_insert = []
    favorites_to_insert = []
    history_to_insert = []

    for email, u in users.items():
        if u.get("is_anonymous"):
            continue  # nao persiste anon
        users_to_insert.append({
            "email": email,
            "is_admin": bool(u.get("is_admin", False)),
            "credits": int(u.get("credits", 10)),
            "queries_used": int(u.get("queries_used", 0)),
            "created_at": u.get("created_at"),
            "last_login": u.get("last_login"),
            "is_anonymous": False,
        })
        for tk in u.get("favorites", []):
            favorites_to_insert.append({"email": email, "ticker": tk.upper().strip()})
        for tk in u.get("history", []):
            history_to_insert.append({"email": email, "ticker": tk.upper().strip()})

    print(f"Migrando {len(users_to_insert)} usuarios, "
          f"{len(favorites_to_insert)} favoritos, "
          f"{len(history_to_insert)} itens de historico...")

    if users_to_insert:
        client.table("users").upsert(users_to_insert).execute()
        print(f"  users: {len(users_to_insert)} upserted")
    if favorites_to_insert:
        client.table("favorites").upsert(favorites_to_insert).execute()
        print(f"  favorites: {len(favorites_to_insert)} upserted")
    if history_to_insert:
        client.table("history").insert(history_to_insert).execute()
        print(f"  history: {len(history_to_insert)} inserted")

    print("Migracao concluida.")


if __name__ == "__main__":
    main()
