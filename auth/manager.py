"""
auth/manager.py — Equity Guard
Gerencia autenticação, cadastro e créditos via users_db.json (mock DB).
Pronto para migração a Supabase: trocar as funções _load_db/_save_db
por chamadas ao cliente Supabase.
"""

import json
import threading
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

from config import USER_QUERY_LIMIT, ADMIN_QUERY_LIMIT

DB_PATH = Path(__file__).parent.parent / "users_db.json"
_lock = threading.Lock()   # thread-safe para o servidor Streamlit


# ── DB helpers ────────────────────────────────────────────────────────────────

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


# ── Operações de usuário ──────────────────────────────────────────────────────

def get_or_create_user(email: str, admin_email: str) -> Dict[str, Any]:
    """
    Retorna o usuário do DB (criando se não existir).
    Admin recebe créditos ilimitados (-1). Novos usuários recebem USER_QUERY_LIMIT.
    """
    with _lock:
        db = _load_db()
        users = db.setdefault("users", {})
        is_admin = bool(admin_email) and email == admin_email.lower()

        if email not in users:
            users[email] = {
                "email": email,
                "is_admin": is_admin,
                "credits": ADMIN_QUERY_LIMIT if is_admin else USER_QUERY_LIMIT,
                "queries_used": 0,
                "created_at": datetime.now().isoformat(),
                "last_login": datetime.now().isoformat(),
                "is_anonymous": False,
            }
        else:
            users[email]["last_login"] = datetime.now().isoformat()
            # Promover para admin se e-mail bater agora
            if is_admin and not users[email].get("is_admin"):
                users[email]["is_admin"] = True
                users[email]["credits"] = ADMIN_QUERY_LIMIT

        _save_db(db)
        return dict(users[email])


def load_user(email: str) -> Optional[Dict[str, Any]]:
    """Carrega dados atualizados do usuário (para refletir créditos após consumo)."""
    with _lock:
        db = _load_db()
        user = db["users"].get(email)
        return dict(user) if user else None


def use_credit(email: str) -> bool:
    """
    Consome 1 crédito do usuário.
    Retorna True se a consulta foi autorizada, False se sem crédito.
    Admin (credits == -1) nunca é bloqueado.
    """
    with _lock:
        db = _load_db()
        user = db["users"].get(email)

        if user is None:
            return False

        if user["credits"] == ADMIN_QUERY_LIMIT:   # ilimitado
            user["queries_used"] += 1
            db["users"][email] = user
            _save_db(db)
            return True

        if user["credits"] <= 0:
            return False

        user["credits"] -= 1
        user["queries_used"] += 1
        db["users"][email] = user
        _save_db(db)
        return True


def has_credits(user: Dict[str, Any]) -> bool:
    """Verifica se o usuário (dict do session_state) pode fazer mais consultas."""
    if user.get("is_anonymous"):
        return user.get("credits", 0) > 0
    return user.get("credits", 0) == ADMIN_QUERY_LIMIT or user.get("credits", 0) > 0


def get_all_users() -> list:
    """
    Retorna lista de todos os usuários para o painel admin.
    Exclui usuários anônimos (sem e-mail real).
    """
    with _lock:
        db = _load_db()
        return [
            dict(u) for u in db["users"].values()
            if not u.get("is_anonymous", False)
        ]


def get_favorites(email: str) -> list:
    """Lista de tickers favoritos do usuário."""
    with _lock:
        db = _load_db()
        user = db["users"].get(email)
        return list(user.get("favorites", [])) if user else []


def add_favorite(email: str, ticker: str) -> None:
    """Adiciona um ticker à watchlist (dedup, no-op se já existir)."""
    ticker = ticker.upper().strip()
    if not ticker:
        return
    with _lock:
        db = _load_db()
        user = db["users"].get(email)
        if not user:
            return
        favs = user.setdefault("favorites", [])
        if ticker not in favs:
            favs.append(ticker)
            _save_db(db)


def remove_favorite(email: str, ticker: str) -> None:
    """Remove um ticker da watchlist."""
    ticker = ticker.upper().strip()
    with _lock:
        db = _load_db()
        user = db["users"].get(email)
        if not user:
            return
        favs = user.setdefault("favorites", [])
        if ticker in favs:
            favs.remove(ticker)
            _save_db(db)


def get_history(email: str) -> list:
    """Últimos tickers consultados (mais recente primeiro)."""
    with _lock:
        db = _load_db()
        user = db["users"].get(email)
        return list(user.get("history", [])) if user else []


def add_history(email: str, ticker: str, max_len: int = 10) -> None:
    """
    Adiciona um ticker ao histórico de consultas.
    Dedup: se já existe, move para o topo. Cap em max_len (padrão 10).
    """
    ticker = ticker.upper().strip()
    if not ticker:
        return
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


def credit_label(user: Dict[str, Any]) -> str:
    """Texto amigável para exibir o saldo de créditos."""
    if user.get("is_anonymous"):
        remaining = user.get("credits", 0)
        return f"👁 Anônimo — {remaining} consulta grátis restante"
    if user.get("is_admin") or user.get("credits") == ADMIN_QUERY_LIMIT:
        return "∞ Acesso Vitalício"
    c = user.get("credits", 0)
    used = user.get("queries_used", 0)
    return f"🔋 {c} crédito{'s' if c != 1 else ''} restante{'s' if c != 1 else ''} (usou {used})"
