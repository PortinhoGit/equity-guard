"""
analytics.py — Equity Guard
Contador de acessos com histórico diário persistido em JSON.
"""

import json
import threading
from datetime import datetime
from pathlib import Path
from typing import Dict, List

DB_PATH = Path(__file__).parent / "analytics_db.json"
_lock = threading.Lock()


def _load() -> Dict:
    if DB_PATH.exists():
        try:
            with open(DB_PATH, encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            pass
    return {"total": 0, "daily": {}}


def _save(db: Dict) -> None:
    try:
        with open(DB_PATH, "w", encoding="utf-8") as f:
            json.dump(db, f, indent=2, ensure_ascii=False)
    except OSError:
        pass


def register_visit() -> Dict:
    """Registra uma visita e retorna stats atuais."""
    today = datetime.now().strftime("%Y-%m-%d")
    with _lock:
        db = _load()
        db["total"] = db.get("total", 0) + 1
        daily = db.setdefault("daily", {})
        daily[today] = daily.get(today, 0) + 1
        _save(db)
        return {"total": db["total"], "today": daily[today], "daily": daily}


def get_stats() -> Dict:
    """Retorna stats sem registrar visita."""
    with _lock:
        db = _load()
        today = datetime.now().strftime("%Y-%m-%d")
        daily = db.get("daily", {})
        return {
            "total": db.get("total", 0),
            "today": daily.get(today, 0),
            "daily": daily,
        }


def get_daily_series(last_n: int = 30) -> List[tuple]:
    """Retorna lista de (date_str, count) dos últimos N dias."""
    with _lock:
        db = _load()
        daily = db.get("daily", {})
        sorted_days = sorted(daily.items(), reverse=True)[:last_n]
        return list(reversed(sorted_days))
