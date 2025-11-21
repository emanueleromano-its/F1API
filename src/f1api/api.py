from __future__ import annotations

import os
from typing import Any, Dict, Optional

import requests


F1OPEN_API_BASE = os.getenv("F1OPEN_API_BASE", "https://api.openf1.org/v1")


def fetch_from_f1open(path: str, params: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
    """Esegue una GET verso l'API F1Open e ritorna il JSON (o None in caso di errore)."""
    url = f"{F1OPEN_API_BASE.rstrip('/')}/{path.lstrip('/')}"
    try:
        resp = requests.get(url, params=params or {}, timeout=10)
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException as exc:
        return {"error": str(exc), "status_code": getattr(exc.response, "status_code", None)}
