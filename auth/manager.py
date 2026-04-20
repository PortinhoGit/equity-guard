"""
auth/manager.py — Equity Guard
Gerencia autenticacao, creditos, favoritos e historico.

Backend:
  - Supabase (primario) quando SUPABASE_URL + SUPABASE_SERVICE_KEY estao em secrets
  - users_db.json local (fallback) para dev sem Supabase configurado

A API publica NAO mudou — as funcoes abaixo continuam com a mesma assinatura
do jeito que app.py as chama.
"""

import json
import threading
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List

from config import USER_QUERY_LIMIT, ADMIN_QUERY_LIMIT
from auth.supabase_client import get_client

DB_PATH = Path(__file__).parent.parent / "users_db.json"
_lock = threading.Lock()


# ── Fallback JSON helpers (so usados quando Supabase nao esta disponivel) ────

def _load_db() -> Dict:
    if DB_PATH.exists():
        try:
            with open(DB_PATH, encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            pass
    return {"users": {}, "meta": {"version": "1.0"}}


def _save_db(db: Dict) -> None:
    with open(DB_PATH, "w", encoding="utf-8") as f:
        json.dump(db, f, indent=2, ensure_ascii=False)


# ── Utils ─────────────────────────────────────────────────────────────────────

def _now_iso() -> str:
    return datetime.now().isoformat()


def _user_to_dict(row: Dict[str, Any]) -> Dict[str, Any]:
    """Garante shape consistente com o que app.py espera (inclui favorites/history)."""
    return {
        "email": row.get("email"),
        "is_admin": bool(row.get("is_admin", False)),
        "credits": int(row.get("credits", 0)),
        "queries_used": int(row.get("queries_used", 0)),
        "created_at": row.get("created_at"),
        "last_login": row.get("last_login"),
        "is_anonymous": bool(row.get("is_anonymous", False)),
    }


# ── API publica ───────────────────────────────────────────────────────────────

def get_or_create_user(email: str, admin_email: str) -> Dict[str, Any]:
    """
    Retorna o usuario (criando se nao existir).
    Admin recebe creditos ilimitados (-1). Novos usuarios recebem USER_QUERY_LIMIT.
    """
    client = get_client()
    email = (email or "").lower().strip()
    is_admin = bool(admin_email) and email == admin_email.lower()

    if client is None:
        # Fallback JSON
        with _lock:
            db = _load_db()
            users = db.setdefault("users", {})
            if email not in users:
                users[email] = {
                    "email": email,
                    "is_admin": is_admin,
                    "credits": ADMIN_QUERY_LIMIT if is_admin else USER_QUERY_LIMIT,
                    "queries_used": 0,
                    "created_at": _now_iso(),
                    "last_login": _now_iso(),
                    "is_anonymous": False,
                }
            else:
                users[email]["last_login"] = _now_iso()
                if is_admin and not users[email].get("is_admin"):
                    users[email]["is_admin"] = True
                    users[email]["credits"] = ADMIN_QUERY_LIMIT
            _save_db(db)
            return dict(users[email])

    # Supabase
    existing = client.table("users").select("*").eq("email", email).limit(1).execute()
    if existing.data:
        row = existing.data[0]
        update = {"last_login": _now_iso()}
        if is_admin and not row.get("is_admin"):
            update["is_admin"] = True
            update["credits"] = ADMIN_QUERY_LIMIT
        client.table("users").update(update).eq("email", email).execute()
        row.update(update)
        return _user_to_dict(row)
    new_row = {
        "email": email,
        "is_admin": is_admin,
        "credits": ADMIN_QUERY_LIMIT if is_admin else USER_QUERY_LIMIT,
        "queries_used": 0,
        "created_at": _now_iso(),
        "last_login": _now_iso(),
        "is_anonymous": False,
    }
    client.table("users").insert(new_row).execute()
    return _user_to_dict(new_row)


def load_user(email: str) -> Optional[Dict[str, Any]]:
    """Carrega dados atualizados do usuario."""
    client = get_client()
    if client is None:
        with _lock:
            db = _load_db()
            u = db["users"].get(email)
            return dict(u) if u else None
    res = client.table("users").select("*").eq("email", email).limit(1).execute()
    return _user_to_dict(res.data[0]) if res.data else None


def use_credit(email: str) -> bool:
    """Consome 1 credito. True se autorizado, False se sem credito."""
    client = get_client()
    if client is None:
        with _lock:
            db = _load_db()
            user = db["users"].get(email)
            if not user:
                return False
            if user["credits"] == ADMIN_QUERY_LIMIT:
                user["queries_used"] += 1
            else:
                if user["credits"] <= 0:
                    return False
                user["credits"] -= 1
                user["queries_used"] += 1
            db["users"][email] = user
            _save_db(db)
            return True

    res = client.table("users").select("credits, queries_used").eq("email", email).limit(1).execute()
    if not res.data:
        return False
    row = res.data[0]
    credits = int(row["credits"])
    queries = int(row["queries_used"])
    if credits == ADMIN_QUERY_LIMIT:
        client.table("users").update({"queries_used": queries + 1}).eq("email", email).execute()
        return True
    if credits <= 0:
        return False
    client.table("users").update({
        "credits": credits - 1,
        "queries_used": queries + 1,
    }).eq("email", email).execute()
    return True


def has_credits(user: Dict[str, Any]) -> bool:
    """Verifica se o usuario (dict do session_state) pode fazer mais consultas."""
    if user.get("is_anonymous"):
        return user.get("credits", 0) > 0
    return user.get("credits", 0) == ADMIN_QUERY_LIMIT or user.get("credits", 0) > 0


def get_all_users() -> list:
    """Lista de usuarios nao-anonimos para o painel admin."""
    client = get_client()
    if client is None:
        with _lock:
            db = _load_db()
            return [
                dict(u) for u in db["users"].values()
                if not u.get("is_anonymous", False)
            ]
    res = client.table("users").select("*").eq("is_anonymous", False).execute()
    return [_user_to_dict(r) for r in (res.data or [])]


def get_favorites(email: str) -> List[str]:
    """Lista de tickers favoritos."""
    client = get_client()
    if client is None:
        with _lock:
            db = _load_db()
            u = db["users"].get(email)
            return list(u.get("favorites", [])) if u else []
    res = client.table("favorites").select("ticker").eq("email", email).execute()
    return [r["ticker"] for r in (res.data or [])]


def add_favorite(email: str, ticker: str) -> None:
    """Adiciona ticker a watchlist (dedup via PK composta)."""
    ticker = ticker.upper().strip()
    if not ticker:
        return
    client = get_client()
    if client is None:
        with _lock:
            db = _load_db()
            user = db["users"].get(email)
            if not user:
                return
            favs = user.setdefault("favorites", [])
            if ticker not in favs:
                favs.append(ticker)
                _save_db(db)
        return
    # upsert para nao falhar se ja existe (PK composta email+ticker)
    try:
        client.table("favorites").upsert({"email": email, "ticker": ticker}).execute()
    except Exception:
        pass


def remove_favorite(email: str, ticker: str) -> None:
    """Remove ticker da watchlist."""
    ticker = ticker.upper().strip()
    client = get_client()
    if client is None:
        with _lock:
            db = _load_db()
            user = db["users"].get(email)
            if not user:
                return
            favs = user.setdefault("favorites", [])
            if ticker in favs:
                favs.remove(ticker)
                _save_db(db)
        return
    client.table("favorites").delete().eq("email", email).eq("ticker", ticker).execute()


def get_history(email: str) -> List[str]:
    """Ultimos tickers consultados (mais recente primeiro)."""
    client = get_client()
    if client is None:
        with _lock:
            db = _load_db()
            u = db["users"].get(email)
            return list(u.get("history", [])) if u else []
    res = (
        client.table("history")
        .select("ticker")
        .eq("email", email)
        .order("accessed_at", desc=True)
        .limit(10)
        .execute()
    )
    # Dedup preservando ordem (mais recente primeiro)
    seen = set()
    out = []
    for r in (res.data or []):
        t = r["ticker"]
        if t not in seen:
            seen.add(t)
            out.append(t)
    return out


def add_history(email: str, ticker: str, max_len: int = 10) -> None:
    """Adiciona ticker ao historico. Dedup preservando so o mais recente."""
    ticker = ticker.upper().strip()
    if not ticker:
        return
    client = get_client()
    if client is None:
        with _lock:
            db = _load_db()
            user = db["users"].get(email)
            if not user:
                return
            hist = user.setdefault("history", [])
            if ticker in hist:
                hist.remove(ticker)
            hist.insert(0, ticker)
            user["history"] = hist[:max_len]
            _save_db(db)
        return
    # Remove entradas antigas do mesmo ticker para esse user e insere a nova.
    client.table("history").delete().eq("email", email).eq("ticker", ticker).execute()
    client.table("history").insert({"email": email, "ticker": ticker}).execute()
    # Corta historico alem de max_len (housekeeping leve; idealmente via cron).
    res = (
        client.table("history")
        .select("id, accessed_at")
        .eq("email", email)
        .order("accessed_at", desc=True)
        .execute()
    )
    rows = res.data or []
    if len(rows) > max_len:
        to_delete = [r["id"] for r in rows[max_len:]]
        client.table("history").delete().in_("id", to_delete).execute()


def credit_label(user: Dict[str, Any]) -> str:
    """Texto amigavel para exibir o saldo de creditos."""
    if user.get("is_anonymous"):
        remaining = user.get("credits", 0)
        return f"👁 Anônimo — {remaining} consulta grátis restante"
    if user.get("is_admin") or user.get("credits") == ADMIN_QUERY_LIMIT:
        return "∞ Acesso Vitalício"
    c = user.get("credits", 0)
    used = user.get("queries_used", 0)
    return f"🔋 {c} crédito{'s' if c != 1 else ''} restante{'s' if c != 1 else ''} (usou {used})"
