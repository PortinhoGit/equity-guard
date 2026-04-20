"""
auth/subscribers.py — Equity Guard
Gerencia assinaturas do briefing diario por e-mail.
"""

import secrets
from typing import Optional, List, Dict, Any
from datetime import datetime

from auth.supabase_client import get_client


def _gen_token() -> str:
    """Gera um token URL-safe de 32 chars para unsubscribe."""
    return secrets.token_urlsafe(24)


def subscribe(email: str) -> Optional[str]:
    """
    Registra um e-mail para receber o briefing diario.
    Retorna o token de cancelamento, ou None em falha.
    Se o e-mail ja existe, reativa a inscricao (is_active=True) e retorna o token existente.
    """
    email = (email or "").strip().lower()
    if not email or "@" not in email:
        return None

    client = get_client()
    if client is None:
        return None

    try:
        existing = client.table("subscribers").select("*").eq("email", email).limit(1).execute()
        if existing.data:
            row = existing.data[0]
            # Reativa se estiver inativo
            if not row["is_active"]:
                client.table("subscribers").update({"is_active": True}).eq("email", email).execute()
            return row["token"]

        token = _gen_token()
        client.table("subscribers").insert({
            "email": email,
            "token": token,
            "is_active": True,
        }).execute()
        return token
    except Exception:
        return None


def unsubscribe(token: str) -> bool:
    """Desativa a inscricao por token. True se encontrou e desativou."""
    if not token:
        return False
    client = get_client()
    if client is None:
        return False
    try:
        res = (
            client.table("subscribers")
            .update({"is_active": False})
            .eq("token", token)
            .execute()
        )
        return bool(res.data)
    except Exception:
        return False


def is_subscribed(email: str) -> bool:
    """Retorna True se o e-mail tem inscricao ativa."""
    email = (email or "").strip().lower()
    if not email:
        return False
    client = get_client()
    if client is None:
        return False
    try:
        res = (
            client.table("subscribers")
            .select("is_active")
            .eq("email", email)
            .limit(1)
            .execute()
        )
        return bool(res.data) and bool(res.data[0]["is_active"])
    except Exception:
        return False


def get_active_subscribers() -> List[Dict[str, Any]]:
    """Lista de assinantes ativos para o job de envio diario."""
    client = get_client()
    if client is None:
        return []
    try:
        res = (
            client.table("subscribers")
            .select("email, token")
            .eq("is_active", True)
            .execute()
        )
        return list(res.data or [])
    except Exception:
        return []


def mark_sent(email: str) -> None:
    """Registra timestamp do ultimo envio."""
    client = get_client()
    if client is None:
        return
    try:
        client.table("subscribers").update({
            "last_email_sent_at": datetime.utcnow().isoformat(),
        }).eq("email", email).execute()
    except Exception:
        pass
