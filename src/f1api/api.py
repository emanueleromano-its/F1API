from __future__ import annotations

import os
from typing import Any, Dict, Optional

import requests

from f1api.cache_repository import CacheRepository


F1OPEN_API_BASE = os.getenv("F1OPEN_API_BASE", "https://api.openf1.org/v1")

# Initialize global cache repository
_cache_repo = None


def get_cache_repo() -> CacheRepository:
    """Get or create the global cache repository instance."""
    global _cache_repo
    if _cache_repo is None:
        ttl = int(os.getenv("CACHE_TTL_SECONDS", "300"))  # Default: 5 minutes
        _cache_repo = CacheRepository(default_ttl_seconds=ttl)
    return _cache_repo


def fetch_from_f1open(
    path: str,
    params: Optional[Dict[str, Any]] = None,
    force_refresh: bool = False
) -> Optional[Dict[str, Any]]:
    """Esegue una GET verso l'API F1Open con caching persistente.
    
    Args:
        path: percorso relativo (senza slash iniziale) es. 'drivers' o 'races/2024'
        params: dizionario di query params
        force_refresh: se True, bypassa la cache e forza una nuova chiamata API
        
    Returns:
        JSON response o dict con errore. Include flag 'from_cache' e 'stale' quando applicabili.
    """
    url = f"{F1OPEN_API_BASE.rstrip('/')}/{path.lstrip('/')}"
    cache = get_cache_repo()
    print (f"Fetching URL: {url} with params: {params} (force_refresh={force_refresh})")
    # 1. Controlla cache (se non force_refresh)
    if not force_refresh:
        cached = cache.get(url, params)
        if cached:
            return cached["body"]
    
    # 2. Prepara headers con ETag per conditional request
    headers = {}
    if not force_refresh:
        cached_stale = cache.get_stale(url, params)
        if cached_stale and cached_stale.get("etag"):
            headers["If-None-Match"] = cached_stale["etag"]
    
    # 3. Esegui chiamata API
    try:
        resp = requests.get(url, params=params or {}, headers=headers, timeout=10)
        
        # 4. Gestisci 304 Not Modified
        if resp.status_code == 304:
            # Riusa body dalla cache, aggiorna solo metadata
            cached_stale = cache.get_stale(url, params)
            if cached_stale:
                # Aggiorna TTL nella cache
                cache.set(
                    url, params,
                    cached_stale["body"],
                    200,
                    dict(resp.headers),
                    cached_stale.get("etag")
                )
                return cached_stale["body"]
        
        resp.raise_for_status()
        
        # 5. Salva risposta in cache
        response_data = resp.json()
        etag = resp.headers.get("ETag")
        cache.set(
            url, params,
            response_data,
            resp.status_code,
            dict(resp.headers),
            etag
        )
        
        return response_data
        
    except requests.RequestException as exc:
        # 6. Fallback: usa cache stale se disponibile
        cached_stale = cache.get_stale(url, params)
        if cached_stale:
            # Ritorna dati stale con warning
            result = cached_stale["body"]
            if isinstance(result, dict):
                result["_cache_warning"] = "Using stale cached data due to API error"
                result["_api_error"] = str(exc)
            return result
        
        # 7. Nessun fallback disponibile: ritorna errore
        return {
            "error": str(exc),
            "status_code": getattr(exc.response, "status_code", None) if hasattr(exc, "response") else None
        }
