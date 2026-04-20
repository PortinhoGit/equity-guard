"""
auth/subscribers.py — Equity Guard
Gerencia assinaturas do briefing diario por e-mail com multiplos horarios.
"""

import secrets
from typing import Optional, List, Dict, Any
from datetime import datetime

from auth.supabase_client import get_client


def _gen_token() -> str:
    return secrets.token_urlsafe(24)


def subscribe(email: str) -> Optional[str]:
    """
    Cria ou reativa inscricao do e-mail. Retorna o token (sempre), nao mexe nos horarios.
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
            if not row["is_active"]:
                client.table("subscribers").update({"is_active": True}).eq("email", email).execute()
            return row["token"]
        token = _gen_token()
        client.table("subscribers").insert({
            "email": email, "token": token, "is_active": True,
        }).execute()
        return token
    except Exception:
        return None


def unsubscribe(token: str) -> bool:
    """Desativa assinatura pelo token. Horarios sao preservados mas ignorados (is_active=false)."""
    if not token:
        return False
    client = get_client()
    if client is None:
        return False
    try:
        res = client.table("subscribers").update({"is_active": False}).eq("token", token).execute()
        return bool(res.data)
    except Exception:
        return False


def is_subscribed(email: str) -> bool:
    email = (email or "").strip().lower()
    if not email:
        return False
    client = get_client()
    if client is None:
        return False
    try:
        res = client.table("subscribers").select("is_active").eq("email", email).limit(1).execute()
        return bool(res.data) and bool(res.data[0]["is_active"])
    except Exception:
        return False


def get_user_hours(email: str) -> List[int]:
    """Lista de horarios BRT (0-23) que o usuario escolheu receber."""
    email = (email or "").strip().lower()
    client = get_client()
    if not email or client is None:
        return []
    try:
        res = (
            client.table("subscriber_hours")
            .select("send_hour")
            .eq("email", email)
            .execute()
        )
        return sorted({int(r["send_hour"]) for r in (res.data or [])})
    except Exception:
        return []


def set_user_hours(email: str, hours: List[int]) -> bool:
    """
    Substitui todos os horarios do usuario pela lista fornecida.
    Retorna True em sucesso, False em falha.
    """
    email = (email or "").strip().lower()
    client = get_client()
    if not email or client is None:
        return False
    # Filtra e valida
    clean = sorted({int(h) for h in hours if 0 <= int(h) <= 23})
    try:
        # Remove tudo
        client.table("subscriber_hours").delete().eq("email", email).execute()
        # Insere novo
        if clean:
            rows = [{"email": email, "send_hour": h} for h in clean]
            client.table("subscriber_hours").insert(rows).execute()
        return True
    except Exception:
        return False


def get_subscribers_for_hour(hour: int) -> List[Dict[str, Any]]:
    """
    Retorna assinantes ATIVOS que pediram para receber naquele horario.
    Cada item: {'email': ..., 'token': ...}
    """
    client = get_client()
    if client is None:
        return []
    try:
        # 1) emails que querem este horario
        hrs = (
            client.table("subscriber_hours")
            .select("email")
            .eq("send_hour", int(hour))
            .execute()
        )
        emails = list({r["email"] for r in (hrs.data or [])})
        if not emails:
            return []
        # 2) apenas os que ainda estao ativos
        subs = (
            client.table("subscribers")
            .select("email, token")
            .in_("email", emails)
            .eq("is_active", True)
            .execute()
        )
        return list(subs.data or [])
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
