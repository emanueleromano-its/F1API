from __future__ import annotations

from typing import Any, Dict, Optional

from flask import Blueprint, request, render_template

from f1api.api import fetch_from_f1open
from f1api.auth_decorators import login_required
from f1api.utils import format_datetime, get_country_flags, get_circuit_urls

races_bp = Blueprint("races", __name__)


@races_bp.route("/races", methods=["GET"])
@login_required
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
    # meeting_key 	session_key 	location 	date_start 	date_end 	session_name 	country_key 	country_code 	country_name 	circuit_key 	circuit_short_name 	gmt_offset 	year
    filtered_items = []
    items = sorted(items, key=lambda x: x.get("date_start", ""), reverse=True)
    for item in items:
        location = item.get("location")
        date_raw = item.get("date_start")
        formatted_date = format_datetime(date_raw)
        filtered_items.append(
            {
                "location": location,
                "date_start": formatted_date,
                "session_name": item.get("session_name"),
                "country_name": item.get("country_name"),
                "circuit_short_name": item.get("circuit_short_name"),
                "meeting_key": item.get("meeting_key"),
            }
        )
    col_tradotto = {
        "location": "Circuito",
        "date_start": "Data Inizio",
        "session_name": "Tipo di gara",
        "country_name": "Nome Paese",
        "circuit_short_name": "Nome Alternativo Circuito"
    }
    country_flags = get_country_flags()
    circuit_urls = get_circuit_urls()
    items = filtered_items
    return render_template("races.html", items=items, col_tradotto=col_tradotto, country_flags=country_flags, circuit_urls=circuit_urls)
