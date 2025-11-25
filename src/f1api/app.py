"""Scaffold Flask application per il progetto F1API.

Contiene una factory `create_app`, una funzione helper per chiamare l'API F1Open
e alcune rotte di esempio (health, drivers, teams, races).

Questo file è un punto di partenza: implementa chiamate HTTP minime e gestione
degli errori in modo semplice. Estendi i route handler e la logica di parsing
secondo le necessità dell'API reale.
"""
from __future__ import annotations

import os
import secrets
from typing import Any, Dict, Optional

from flask import Flask
from f1api.routes.drivers import drivers_bp
from f1api.routes.races import races_bp
from f1api.routes.main import main_bp
from f1api.routes.driver import driver_bp
from f1api.routes.race import race_bp
from f1api.routes.teams import teams_bp
from f1api.routes.auth import auth_bp
from f1api.api import F1OPEN_API_BASE


def create_app(test_config: Optional[Dict[str, Any]] = None) -> Flask:
    """Factory per creare l'app Flask."""
    app = Flask(__name__, instance_relative_config=False)

    # Configure session security
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", secrets.token_hex(32))
    app.config["SESSION_COOKIE_SECURE"] = os.getenv("SESSION_COOKIE_SECURE", "False").lower() == "true"
    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
    app.config["PERMANENT_SESSION_LIFETIME"] = 3600  # 1 hour

    if test_config:
        app.config.update(test_config)

    def safe_color(value: Any) -> str:
        """Ritorna un colore esadecimale valido o un default.

        Manteniamo la semplice logica esistente: se il valore è una stringa
        con 6 caratteri hex lo normalizziamo con '#' e minuscolo, altrimenti
        ritorniamo un colore di default.
        """
        try:
            v = str(value).strip()
        except Exception:
            return "#CCCCCC"
        if v.startswith("#") and len(v) == 7:
            return v
        # accetta valori senza '#', es. '3671C6'
        if len(v) == 6 and all(c in "0123456789abcdefABCDEF" for c in v):
            return f"#{v.lower()}"
        return "#CCCCCC"

    app.jinja_env.filters["safe_color"] = safe_color

    # Middleware to track page visits
    @app.after_request
    def track_page_visit(response):
        """Track authenticated user page visits."""
        from flask import session, request
        from f1api.auth_repository import get_auth_repo
        
        # Only track successful GET requests for logged-in users
        if (response.status_code == 200 and 
            request.method == "GET" and 
            "user_id" in session):
            
            # Skip tracking for static files, API endpoints, and auth pages
            skip_paths = ["/static/", "/api", "/auth/", "/cache/"]
            if not any(request.path.startswith(path) for path in skip_paths):
                try:
                    auth_repo = get_auth_repo()
                    # Map common routes to friendly titles
                    page_titles = {
                        "/": "Home",
                        "/drivers": "Drivers List",
                        "/teams": "Teams",
                        "/races": "Races Calendar",
                        "/history": "Navigation History"
                    }
                    
                    # For driver detail pages
                    if request.path.startswith("/driver/"):
                        page_title = f"Driver #{request.path.split('/')[-1]}"
                    else:
                        page_title = page_titles.get(request.path, request.path)
                    
                    auth_repo.track_page_visit(
                        session["user_id"],
                        request.path,
                        page_title
                    )
                except Exception:
                    # Don't fail the request if tracking fails
                    pass
        
        return response

    # register blueprints
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(drivers_bp)
    app.register_blueprint(races_bp)
    # blueprint con route /driver/<driver_number> (alias singolare)
    app.register_blueprint(driver_bp)
    # blueprint con route /race/<meeting_key> per dettaglio meeting/classifiche
    app.register_blueprint(race_bp)
    # blueprint con route /teams per visualizzare scuderie e piloti
    app.register_blueprint(teams_bp)


    return app


if __name__ == "__main__":
    app = create_app()
    # In sviluppo abilita debug. In produzione usa un WSGI server (gunicorn/uvicorn)
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)), debug=True)
