"""Scaffold Flask application per il progetto F1API."""
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

    # Configura la sicurezza della sessione
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", secrets.token_hex(32))
    app.config["SESSION_COOKIE_SECURE"] = os.getenv("SESSION_COOKIE_SECURE", "False").lower() == "true"
    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
    app.config["PERMANENT_SESSION_LIFETIME"] = 3600  # 1 ora

    if test_config:
        app.config.update(test_config)

    def safe_color(value: Any) -> str:
        """Ritorna un colore esadecimale valido o un default.

        L'api ritorna un hex con 6 caratteri 
        quindi lo normalio con '#' e minuscolo, altrimenti
        ritorno un colore di default.
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

    # Middleware per tracciare le visite alle pagine
    @app.after_request
    def track_page_visit(response):
        """Registra le visite di pagina da parte di utenti autenticati."""
        from flask import session, request
        from f1api.auth_repository import get_auth_repo
        
    # Traccia solo le richieste GET riuscite effettuate da utenti autenticati
        if (response.status_code == 200 and 
            request.method == "GET" and 
            "user_id" in session):
            
            # Salta il tracciamento per file statici, endpoint API e pagine di autenticazione
            skip_paths = ["/static/", "/api", "/auth/", "/cache/"]
            if not any(request.path.startswith(path) for path in skip_paths):
                try:
                    auth_repo = get_auth_repo()
                    # Mappa percorsi comuni a titoli leggibili
                    page_titles = {
                        "/": "Home",
                        "/drivers": "Drivers List",
                        "/teams": "Teams",
                        "/races": "Races Calendar",
                        "/history": "Navigation History"
                    }
                    
                    # Per le pagine di dettaglio pilota
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
                    # Non far fallire la richiesta se il tracciamento fallisce
                    pass
        
        return response

    # registra i blueprint
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

    # Pulisce automaticamente le voci di cache scadute all'avvio
    from f1api.api import get_cache_repo
    try:
        cache = get_cache_repo()
        expired_count = cache.cleanup_expired()
        if expired_count > 0:
            print(f"✓ Cache cleanup: removed {expired_count} expired entries")
    except Exception as e:
        print(f"⚠ Cache cleanup failed: {e}")

    return app


if __name__ == "__main__":
    app = create_app()
    # In sviluppo abilita debug. In produzione usa un WSGI server (gunicorn/uvicorn)
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)), debug=True)
