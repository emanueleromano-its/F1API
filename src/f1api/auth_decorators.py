"""Authentication decorators and utilities for F1API."""
from __future__ import annotations

from functools import wraps
from typing import Callable, Any

from flask import session, redirect, url_for, flash


def login_required(f: Callable) -> Callable:
    """Decorator to protect routes requiring authentication.
    
    Usage:
        @app.route('/protected')
        @login_required
        def protected_route():
            return "This requires login"
    """
    @wraps(f)
    def decorated_function(*args: Any, **kwargs: Any) -> Any:
        if "user_id" not in session:
            flash("Please log in to access this page.", "warning")
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)
    return decorated_function


def get_current_user() -> dict | None:
    """Get current logged-in user from session.
    
    Returns:
        User dict if logged in, None otherwise
    """
    if "user_id" in session:
        from f1api.auth_repository import get_auth_repo
        auth_repo = get_auth_repo()
        return auth_repo.get_user_by_id(session["user_id"])
    return None


def is_authenticated() -> bool:
    """Check if user is authenticated.
    
    Returns:
        True if user is logged in, False otherwise
    """
    return "user_id" in session
