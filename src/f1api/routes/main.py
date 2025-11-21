from __future__ import annotations

from typing import Any, Dict, Optional

from flask import Blueprint, jsonify

from f1api.api import fetch_from_f1open

main_bp = Blueprint("main", __name__)


@main_bp.route("/", methods=["GET"])
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


@main_bp.route("/position", methods=["GET"])
def position():
    data = fetch_from_f1open("position")
    return jsonify(data)
