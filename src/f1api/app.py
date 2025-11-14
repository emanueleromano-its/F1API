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
from flask import Flask, jsonify, request


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


    @app.route("/health", methods=["GET"])
    def health():
        return jsonify({"status": "ok"})


    @app.route("/drivers", methods=["GET"])
    def drivers():
        """Esempio: /drivers?search=alonso

        Il comportamento concreto dipende dal formato dell'API F1Open.
        Qui forwardiamo semplicemente il parametro `search` come query.
        """
        q = request.args.get("search")
        params = {"search": q} if q else {}
        data = fetch_from_f1open("drivers", params=params)
        return jsonify(data)


    @app.route("/drivers/<driver_number>", methods=["GET"])
    def driver_detail(driver_number: str):
        data = fetch_from_f1open(f"drivers?driver_number={driver_number}")
        return jsonify(data)


    @app.route("/teams", methods=["GET"])
    def teams():
        data = fetch_from_f1open("teams")
        return jsonify(data)


    @app.route("/races", methods=["GET"])
    def races():
        season = request.args.get("season")
        path = "races"
        if season:
            path = f"races/{season}"
        data = fetch_from_f1open(path)
        return jsonify(data)


    return app


if __name__ == "__main__":
    app = create_app()
    # In sviluppo abilita debug. In produzione usa un WSGI server (gunicorn/uvicorn)
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)), debug=True)
