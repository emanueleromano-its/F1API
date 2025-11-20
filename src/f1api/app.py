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

import requests
from flask import Flask, jsonify, request, render_template


F1OPEN_API_BASE = os.getenv("F1OPEN_API_BASE", "https://api.openf1.org/v1")


def fetch_from_f1open(path: str, params: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
    """Esegue una GET verso l'API F1Open e ritorna il JSON (o None in caso di errore).

    path: percorso relativo (senza slash iniziale) es. 'drivers' o 'races/2024'.
    params: dizionario di query params.
    """
    url = f"{F1OPEN_API_BASE.rstrip('/')}/{path.lstrip('/')}"
    try:
        resp = requests.get(url, params=params or {}, timeout=10)
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException as exc:
        # Log più avanzato può essere aggiunto qui
        return {"error": str(exc), "status_code": getattr(exc.response, "status_code", None)}


def create_app(test_config: Optional[Dict[str, Any]] = None) -> Flask:
    """Factory per creare l'app Flask."""
    app = Flask(__name__, instance_relative_config=False)

    if test_config:
        app.config.update(test_config)


    @app.route("/", methods=["GET"])
    def index():
        return jsonify({
            "service": "F1API (scaffold)",
            "endpoints": [
                {"path": "/drivers", "desc": "Elenca o cerca piloti"},
                {"path": "/drivers/<id>", "desc": "Dettagli pilota"},
                {"path": "/teams", "desc": "Elenca i team"},
                {"path": "/races", "desc": "Elenca le gare"},
            ],
        })

    @app.route("/drivers", methods=["GET"])
    def drivers():
        """Esempio: /drivers?search=alonso

        Il comportamento concreto dipende dal formato dell'API F1Open.
        Qui forwardiamo semplicemente il parametro `search` come query.
        """
        q = request.args.get("search")
        params = {"search": q} if q else {}
        data = fetch_from_f1open("drivers", params=params)
        
        items = []
        if isinstance(data, list):
            items = data
        elif isinstance(data, dict):
            if data.get("error"):
                return render_template("drivers.html", error=data.get("error"), items=[])
            for v in data.values():
                if isinstance(v, list):
                    items = v
                    break
            if not items:
                items = [data]
        items = sorted(items, key=lambda x: x.get("session_key", ""), reverse=True)

        # colonne da mostrare: escludiamo alcune chiavi non rilevanti per la tabella
        exclude = {"meeting_key", "session_key", "broadcast_name", "team_colour", "country_code", "first_name", "last_name"}
        cols = []
        if items:
            first = items[0]
            if isinstance(first, dict):
                cols = [c for c in list(first.keys()) if c not in exclude]

        return render_template("drivers.html", items=items, cols=cols)


    @app.route("/drivers/<driver_number>", methods=["GET"])
    def driver_detail(driver_number: str):
        data = fetch_from_f1open(f"drivers?driver_number={driver_number}")
        return jsonify(data)


    @app.route("/position", methods=["GET"])
    def position():
        data = fetch_from_f1open("position")
        return jsonify(data)


    @app.route("/races", methods=["GET"])
    def races():
        """Renderizza una pagina HTML con la lista delle gare (o altri dati restituiti dall'API)."""
        season = request.args.get("season")
        path = "sessions?session_type=Race"
        if season:
            path = f"sessions/{season}"
        data = fetch_from_f1open(path)

        # Normalizziamo i dati: cerchiamo una lista di elementi da mostrare
        items = []
        if isinstance(data, list):
            items = data
        elif isinstance(data, dict):
            # se c'è un errore mostriamolo nella pagina
            if data.get("error"):
                return render_template("races.html", error=data.get("error"), items=[])
            # cerchiamo la prima value che sia una lista (es. {'races': [...]})
            for v in data.values():
                if isinstance(v, list):
                    items = v
                    break
            if not items:
                # fallback: mostriamo il dict come singolo elemento
                items = [data]

        return render_template("races.html", items=items)


    return app


if __name__ == "__main__":
    app = create_app()
    # In sviluppo abilita debug. In produzione usa un WSGI server (gunicorn/uvicorn)
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)), debug=True)
