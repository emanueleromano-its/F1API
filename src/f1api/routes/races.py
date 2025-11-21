from __future__ import annotations

from typing import Any, Dict, Optional

from flask import Blueprint, request, render_template

from f1api.api import fetch_from_f1open

races_bp = Blueprint("races", __name__)


@races_bp.route("/races", methods=["GET"])
def races():
    season = request.args.get("season")
    path = "sessions?session_type=Race"
    if season:
        path = f"sessions/{season}"
    data = fetch_from_f1open(path)

    items = []
    if isinstance(data, list):
        items = data
    elif isinstance(data, dict):
        if data.get("error"):
            return render_template("races.html", error=data.get("error"), items=[])
        for v in data.values():
            if isinstance(v, list):
                items = v
                break
        if not items:
            items = [data]

    return render_template("races.html", items=items)
