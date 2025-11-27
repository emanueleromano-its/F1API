"""Decorator e utility per l'autenticazione in F1API."""
from __future__ import annotations

from functools import wraps
from typing import Callable, Any

from flask import session, redirect, url_for, flash


def login_required(f: Callable) -> Callable:
    """Decorator per proteggere le route che richiedono autenticazione.

    Usage:
        @app.route('/protected')
        @login_required
        def protected_route():
            return "Richiede il login"
    """
    @wraps(f)
    def decorated_function(*args: Any, **kwargs: Any) -> Any:
        if "user_id" not in session:
            flash("Please log in to access this page.", "warning")
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)
    return decorated_function


def get_current_user() -> dict | None:
    """Recupera l'utente attualmente loggato dalla sessione.

    Ritorna:
        Dizionario utente se loggato, altrimenti None
    """
    if "user_id" in session:
        from f1api.auth_repository import get_auth_repo
        auth_repo = get_auth_repo()
        return auth_repo.get_user_by_id(session["user_id"])
    return None


def is_authenticated() -> bool:
    """Verifica se l'utente è autenticato.

    Ritorna:
        True se l'utente è loggato, False altrimenti
    """
    return "user_id" in session
