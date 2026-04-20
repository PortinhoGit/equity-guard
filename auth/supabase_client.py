"""
auth/supabase_client.py — Equity Guard
Cliente Supabase lazy-init. Le credenciais de st.secrets.

Se os secrets nao estiverem configurados, get_client() retorna None e
o manager.py faz fallback para o users_db.json local (comportamento pre-migracao).
"""

from typing import Optional

_client = None
_checked = False


def get_client():
    """
    Retorna um cliente Supabase (singleton) ou None se nao configurado.
    Usa a SERVICE_ROLE_KEY para bypass de RLS (operacoes admin do backend).
    """
    global _client, _checked
    if _checked:
        return _client
    _checked = True
    try:
        import streamlit as st
        url = st.secrets.get("SUPABASE_URL")
        key = st.secrets.get("SUPABASE_SERVICE_KEY")
        if not url or not key:
            return None
        from supabase import create_client
        _client = create_client(url, key)
    except Exception:
        _client = None
    return _client


def is_available() -> bool:
    """True se o cliente Supabase esta configurado e operacional."""
    return get_client() is not None
