"""Scaffold Flask application per il progetto F1API.

Contiene una factory `create_app`, una funzione helper per chiamare l'API F1Open
e alcune rotte di esempio (health, drivers, teams, races).

Questo file è un punto di partenza: implementa chiamate HTTP minime e gestione
degli errori in modo semplice. Estendi i route handler e la logica di parsing
secondo le necessità dell'API reale.
"""
from __future__ import annotations

import os
from typing import Any, Dict, Optional

from flask import Flask
from f1api.routes.drivers import drivers_bp
from f1api.routes.races import races_bp
from f1api.routes.main import main_bp
from f1api.api import F1OPEN_API_BASE


def create_app(test_config: Optional[Dict[str, Any]] = None) -> Flask:
    """Factory per creare l'app Flask."""
    app = Flask(__name__, instance_relative_config=False)

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

    # register blueprints
    app.register_blueprint(main_bp)
    app.register_blueprint(drivers_bp)
    app.register_blueprint(races_bp)


    return app


if __name__ == "__main__":
    app = create_app()
    # In sviluppo abilita debug. In produzione usa un WSGI server (gunicorn/uvicorn)
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)), debug=True)
