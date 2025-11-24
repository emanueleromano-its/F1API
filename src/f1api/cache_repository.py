"""Cache repository module for F1API.

Provides persistent SQLite-based caching for API responses with:
- TTL-based expiration
- ETag support for conditional requests
- Thread-safe operations
- Fallback to stale cache on API errors
- Configurable cache invalidation
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
    """Thread-safe SQLite cache for API responses."""

    def __init__(self, db_path: Optional[str] = None, default_ttl_seconds: int = 300):
        """Initialize cache repository.
        
        Args:
            db_path: Path to SQLite database file (default: ./data/cache.db)
            default_ttl_seconds: Default TTL for cached entries (default: 300s = 5min)
        """
        self.db_path = db_path or os.getenv("CACHE_DB_PATH", "./data/cache.db")
        self.default_ttl = default_ttl_seconds
        self._local = threading.local()
        self._lock = threading.Lock()
        self._ensure_db()

    def _ensure_db(self) -> None:
        """Create database file and schema if not exists."""
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
        """Get thread-local database connection."""
        if not hasattr(self._local, "conn"):
            self._local.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self._local.conn.row_factory = sqlite3.Row
        return self._local.conn

    @staticmethod
    def _make_resource_key(url: str, params: Optional[Dict[str, Any]] = None) -> str:
        """Generate unique cache key from URL and params.
        
        Args:
            url: Full API URL
            params: Query parameters dict
            
        Returns:
            SHA256 hash of normalized URL+params
        """
        normalized = f"{url}?{json.dumps(params or {}, sort_keys=True)}"
        return hashlib.sha256(normalized.encode()).hexdigest()

    def get(self, url: str, params: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """Retrieve cached response if valid.
        
        Args:
            url: API URL
            params: Query parameters
            
        Returns:
            Cached response dict or None if not found/expired
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
        """Retrieve cached response even if expired (for fallback).
        
        Args:
            url: API URL
            params: Query parameters
            
        Returns:
            Cached response dict or None if not found
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
        """Save API response to cache.
        
        Args:
            url: API URL
            params: Query parameters
            response_body: Response data (will be JSON serialized)
            status_code: HTTP status code
            headers: Response headers
            etag: ETag value for conditional requests
            ttl_seconds: TTL override (default uses default_ttl)
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
        """Invalidate cache entries.
        
        Args:
            url: Specific URL to invalidate (if None, clear all)
            params: Query parameters (only used if url is specified)
            
        Returns:
            Number of entries deleted
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
        """Remove expired entries from cache.
        
        Returns:
            Number of entries deleted
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
        """Get cache statistics.
        
        Returns:
            Dict with total entries, expired count, size
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
        """Close database connection."""
        if hasattr(self._local, "conn"):
            self._local.conn.close()
            delattr(self._local, "conn")
