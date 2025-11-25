"""Authentication repository module for F1API.

Provides user authentication and management with:
- Secure password hashing (bcrypt)
- User registration and login
- SQLite-based user storage
- Thread-safe operations
"""
from __future__ import annotations

import os
import sqlite3
import threading
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

import bcrypt


class AuthRepository:
    """Thread-safe SQLite repository for user authentication."""

    def __init__(self, db_path: Optional[str] = None):
        """Initialize auth repository.
        
        Args:
            db_path: Path to SQLite database file (default: ./data/users.db)
        """
        self.db_path = db_path or os.getenv("AUTH_DB_PATH", "./data/users.db")
        self._local = threading.local()
        self._lock = threading.Lock()
        self._ensure_db()

    def _ensure_db(self) -> None:
        """Create database file and schema if not exists."""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    last_login TEXT
                )
            """)
            conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_username ON users(username)")
            conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_email ON users(email)")
            
            # Create page_history table for tracking navigation
            conn.execute("""
                CREATE TABLE IF NOT EXISTS page_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    page_url TEXT NOT NULL,
                    page_title TEXT,
                    visited_at TEXT NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_user_history ON page_history(user_id, visited_at DESC)")
            
            conn.commit()
            conn.close()

    def _get_connection(self) -> sqlite3.Connection:
        """Get thread-local database connection."""
        if not hasattr(self._local, "conn") or self._local.conn is None:
            self._local.conn = sqlite3.connect(self.db_path)
            self._local.conn.row_factory = sqlite3.Row
        return self._local.conn

    @staticmethod
    def hash_password(password: str) -> str:
        """Hash password using bcrypt.
        
        Args:
            password: Plain text password
            
        Returns:
            Hashed password as string
        """
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')

    @staticmethod
    def verify_password(password: str, password_hash: str) -> bool:
        """Verify password against hash.
        
        Args:
            password: Plain text password
            password_hash: Stored password hash
            
        Returns:
            True if password matches, False otherwise
        """
        try:
            return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
        except Exception:
            return False

    def create_user(self, username: str, email: str, password: str) -> Optional[int]:
        """Create new user.
        
        Args:
            username: Unique username
            email: Unique email address
            password: Plain text password (will be hashed)
            
        Returns:
            User ID if successful, None if username/email already exists
        """
        password_hash = self.hash_password(password)
        created_at = datetime.utcnow().isoformat()
        
        try:
            with self._lock:
                conn = self._get_connection()
                cursor = conn.execute(
                    """
                    INSERT INTO users (username, email, password_hash, created_at)
                    VALUES (?, ?, ?, ?)
                    """,
                    (username, email, password_hash, created_at)
                )
                conn.commit()
                return cursor.lastrowid
        except sqlite3.IntegrityError:
            # Username or email already exists
            return None

    def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """Get user by username.
        
        Args:
            username: Username to search for
            
        Returns:
            User dict with id, username, email, created_at, last_login or None
        """
        conn = self._get_connection()
        cursor = conn.execute(
            "SELECT id, username, email, created_at, last_login FROM users WHERE username = ?",
            (username,)
        )
        row = cursor.fetchone()
        if row:
            return dict(row)
        return None

    def get_user_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user by ID.
        
        Args:
            user_id: User ID to search for
            
        Returns:
            User dict with id, username, email, created_at, last_login or None
        """
        conn = self._get_connection()
        cursor = conn.execute(
            "SELECT id, username, email, created_at, last_login FROM users WHERE id = ?",
            (user_id,)
        )
        row = cursor.fetchone()
        if row:
            return dict(row)
        return None

    def authenticate(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """Authenticate user with username and password.
        
        Args:
            username: Username
            password: Plain text password
            
        Returns:
            User dict if authentication successful, None otherwise
        """
        conn = self._get_connection()
        cursor = conn.execute(
            "SELECT id, username, email, password_hash, created_at, last_login FROM users WHERE username = ?",
            (username,)
        )
        row = cursor.fetchone()
        
        if not row:
            return None
        
        password_hash = row["password_hash"]
        if not self.verify_password(password, password_hash):
            return None
        
        # Update last login
        self.update_last_login(row["id"])
        
        # Return user without password_hash
        return {
            "id": row["id"],
            "username": row["username"],
            "email": row["email"],
            "created_at": row["created_at"],
            "last_login": row["last_login"]
        }

    def update_last_login(self, user_id: int) -> None:
        """Update user's last login timestamp.
        
        Args:
            user_id: User ID
        """
        last_login = datetime.utcnow().isoformat()
        with self._lock:
            conn = self._get_connection()
            conn.execute(
                "UPDATE users SET last_login = ? WHERE id = ?",
                (last_login, user_id)
            )
            conn.commit()

    def username_exists(self, username: str) -> bool:
        """Check if username already exists.
        
        Args:
            username: Username to check
            
        Returns:
            True if exists, False otherwise
        """
        conn = self._get_connection()
        cursor = conn.execute(
            "SELECT COUNT(*) as count FROM users WHERE username = ?",
            (username,)
        )
        row = cursor.fetchone()
        return row["count"] > 0

    def email_exists(self, email: str) -> bool:
        """Check if email already exists.
        
        Args:
            email: Email to check
            
        Returns:
            True if exists, False otherwise
        """
        conn = self._get_connection()
        cursor = conn.execute(
            "SELECT COUNT(*) as count FROM users WHERE email = ?",
            (email,)
        )
        row = cursor.fetchone()
        return row["count"] > 0

    def track_page_visit(self, user_id: int, page_url: str, page_title: Optional[str] = None) -> None:
        """Track a page visit for a user.
        
        Args:
            user_id: User ID
            page_url: URL of the visited page
            page_title: Optional title of the page
        """
        visited_at = datetime.utcnow().isoformat()
        with self._lock:
            conn = self._get_connection()
            conn.execute(
                """
                INSERT INTO page_history (user_id, page_url, page_title, visited_at)
                VALUES (?, ?, ?, ?)
                """,
                (user_id, page_url, page_title, visited_at)
            )
            conn.commit()

    def get_user_history(self, user_id: int, limit: int = 50) -> list:
        """Get page visit history for a user.
        
        Args:
            user_id: User ID
            limit: Maximum number of records to return (default: 50)
            
        Returns:
            List of history records with id, page_url, page_title, visited_at
        """
        conn = self._get_connection()
        cursor = conn.execute(
            """
            SELECT id, page_url, page_title, visited_at
            FROM page_history
            WHERE user_id = ?
            ORDER BY visited_at DESC
            LIMIT ?
            """,
            (user_id, limit)
        )
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

    def clear_user_history(self, user_id: int) -> int:
        """Clear all history for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            Number of records deleted
        """
        with self._lock:
            conn = self._get_connection()
            cursor = conn.execute(
                "DELETE FROM page_history WHERE user_id = ?",
                (user_id,)
            )
            conn.commit()
            return cursor.rowcount

    def close(self) -> None:
        """Close database connection for current thread."""
        if hasattr(self._local, "conn") and self._local.conn:
            self._local.conn.close()
            self._local.conn = None


# Global instance
_auth_repo: Optional[AuthRepository] = None


def get_auth_repo() -> AuthRepository:
    """Get or create global AuthRepository instance."""
    global _auth_repo
    if _auth_repo is None:
        _auth_repo = AuthRepository()
    return _auth_repo
