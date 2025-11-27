"""Repository di cache per F1API.

Fornisce caching persistente su SQLite per le risposte API con:
- scadenza basata su TTL
- supporto ETag per richieste condizionali
- operazioni thread-safe
- fallback su cache obsoleta in caso di errori API
- invalidazione configurabile della cache
"""
from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Optional, Tuple


class CacheRepository:
    """Cache SQLite thread-safe per le risposte API."""

    def __init__(self, db_path: Optional[str] = None, default_ttl_seconds: int = 300):
        """Inizializza il repository di cache.

        Argomenti:
            db_path: percorso del file SQLite (default: ./data/cache.db)
            default_ttl_seconds: TTL di default per le voci in cache (default: 300s)
        """
        self.db_path = db_path or os.getenv("CACHE_DB_PATH", "./data/cache.db")
        self.default_ttl = default_ttl_seconds
        self._local = threading.local()
        self._lock = threading.Lock()
        self._ensure_db()

    def _ensure_db(self) -> None:
        """Crea il file del database e lo schema se non esistono."""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS api_cache (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    resource_key TEXT UNIQUE NOT NULL,
                    response_body TEXT NOT NULL,
                    status_code INTEGER NOT NULL,
                    headers TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    expires_at TEXT,
                    etag TEXT
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_resource_key ON api_cache(resource_key)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_expires_at ON api_cache(expires_at)")
            conn.commit()
            conn.close()

    def _get_connection(self) -> sqlite3.Connection:
        """Ottiene la connessione al database locale al thread."""
        if not hasattr(self._local, "conn"):
            self._local.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self._local.conn.row_factory = sqlite3.Row
        return self._local.conn

    @staticmethod
    def _make_resource_key(url: str, params: Optional[Dict[str, Any]] = None) -> str:
        """Genera una chiave univoca di cache da URL e parametri.

        Argomenti:
            url: URL completo dell'API
            params: dizionario dei parametri di query

        Ritorna:
            hash SHA256 della stringa normalizzata URL+params
        """
        normalized = f"{url}?{json.dumps(params or {}, sort_keys=True)}"
        return hashlib.sha256(normalized.encode()).hexdigest()

    def get(self, url: str, params: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """Recupera la risposta in cache se ancora valida.

        Argomenti:
            url: URL dell'API
            params: parametri di query

        Ritorna:
            Dizionario della risposta in cache o None se non trovata/scaduta
        """
        key = self._make_resource_key(url, params)
        conn = self._get_connection()
        
        row = conn.execute(
            "SELECT * FROM api_cache WHERE resource_key = ?",
            (key,)
        ).fetchone()
        
        if not row:
            return None
        
        # Check expiration
        expires_at = row["expires_at"]
        if expires_at:
            expires_dt = datetime.fromisoformat(expires_at)
            if datetime.utcnow() > expires_dt:
                return None  # Expired
        
        return {
            "body": json.loads(row["response_body"]),
            "status_code": row["status_code"],
            "headers": json.loads(row["headers"]) if row["headers"] else {},
            "etag": row["etag"],
            "cached_at": row["updated_at"],
            "from_cache": True
        }

    def get_stale(self, url: str, params: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """Recupera la risposta in cache anche se scaduta (per fallback).

        Argomenti:
            url: URL dell'API
            params: parametri di query

        Ritorna:
            Dizionario della risposta in cache o None se non trovata
        """
        key = self._make_resource_key(url, params)
        conn = self._get_connection()
        
        row = conn.execute(
            "SELECT * FROM api_cache WHERE resource_key = ?",
            (key,)
        ).fetchone()
        
        if not row:
            return None
        
        return {
            "body": json.loads(row["response_body"]),
            "status_code": row["status_code"],
            "headers": json.loads(row["headers"]) if row["headers"] else {},
            "etag": row["etag"],
            "cached_at": row["updated_at"],
            "from_cache": True,
            "stale": True
        }

    def set(
        self,
        url: str,
        params: Optional[Dict[str, Any]],
        response_body: Any,
        status_code: int,
        headers: Optional[Dict[str, str]] = None,
        etag: Optional[str] = None,
        ttl_seconds: Optional[int] = None
    ) -> None:
        """Salva la risposta API nella cache.

        Argomenti:
            url: URL dell'API
            params: parametri di query
            response_body: dati della risposta (verranno serializzati in JSON)
            status_code: codice di stato HTTP
            headers: header della risposta
            etag: valore ETag per richieste condizionali
            ttl_seconds: override del TTL (usa default_ttl se None)
        """
        key = self._make_resource_key(url, params)
        ttl = ttl_seconds if ttl_seconds is not None else self.default_ttl
        
        now = datetime.utcnow()
        expires_at = now + timedelta(seconds=ttl)
        
        conn = self._get_connection()
        with self._lock:
            conn.execute("""
                INSERT INTO api_cache (
                    resource_key, response_body, status_code, headers,
                    created_at, updated_at, expires_at, etag
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(resource_key) DO UPDATE SET
                    response_body = excluded.response_body,
                    status_code = excluded.status_code,
                    headers = excluded.headers,
                    updated_at = excluded.updated_at,
                    expires_at = excluded.expires_at,
                    etag = excluded.etag
            """, (
                key,
                json.dumps(response_body),
                status_code,
                json.dumps(headers) if headers else None,
                now.isoformat(),
                now.isoformat(),
                expires_at.isoformat(),
                etag
            ))
            conn.commit()

    def invalidate(self, url: Optional[str] = None, params: Optional[Dict[str, Any]] = None) -> int:
        """Invalidare voci di cache.

        Argomenti:
            url: URL specifico da invalidare (se None, cancella tutte le voci)
            params: parametri di query (usati solo se specificato l'url)

        Ritorna:
            Numero di voci cancellate
        """
        conn = self._get_connection()
        with self._lock:
            if url:
                key = self._make_resource_key(url, params)
                cursor = conn.execute("DELETE FROM api_cache WHERE resource_key = ?", (key,))
            else:
                cursor = conn.execute("DELETE FROM api_cache")
            conn.commit()
            return cursor.rowcount

    def cleanup_expired(self) -> int:
        """Rimuove le voci scadute dalla cache.

        Ritorna:
            Numero di voci eliminate
        """
        conn = self._get_connection()
        with self._lock:
            now = datetime.utcnow().isoformat()
            cursor = conn.execute(
                "DELETE FROM api_cache WHERE expires_at IS NOT NULL AND expires_at < ?",
                (now,)
            )
            conn.commit()
            return cursor.rowcount

    def stats(self) -> Dict[str, Any]:
        """Ottiene statistiche della cache.

        Ritorna:
            Dizionario con voci totali, scadute, dimensione
        """
        conn = self._get_connection()
        total = conn.execute("SELECT COUNT(*) as count FROM api_cache").fetchone()["count"]
        
        now = datetime.utcnow().isoformat()
        expired = conn.execute(
            "SELECT COUNT(*) as count FROM api_cache WHERE expires_at IS NOT NULL AND expires_at < ?",
            (now,)
        ).fetchone()["count"]
        
        # Get DB file size
        db_size = Path(self.db_path).stat().st_size if Path(self.db_path).exists() else 0
        
        return {
            "total_entries": total,
            "expired_entries": expired,
            "valid_entries": total - expired,
            "db_size_bytes": db_size,
            "db_path": self.db_path
        }

    def close(self) -> None:
        """Chiude la connessione al database."""
        if hasattr(self._local, "conn"):
            self._local.conn.close()
            delattr(self._local, "conn")
