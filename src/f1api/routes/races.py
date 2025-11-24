from __future__ import annotations

from typing import Any, Dict, Optional

from flask import Blueprint, request, render_template

from f1api.api import fetch_from_f1open
from datetime import datetime

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
    # meeting_key 	session_key 	location 	date_start 	date_end 	session_name 	country_key 	country_code 	country_name 	circuit_key 	circuit_short_name 	gmt_offset 	year
    filtered_items = []
    items = sorted(items, key=lambda x: x.get("date_start", ""), reverse=True)
    for item in items:
        location = item.get("location")
        date_raw = item.get("date_start")
        formatted_date = None
        if date_raw:
            try:
                dt = datetime.fromisoformat(date_raw)
                formatted_date = dt.strftime("%d/%m/%Y %H:%M")
            except Exception:
                try:
                    # fallback if timezone-less ISO
                    dt = datetime.strptime(date_raw, "%Y-%m-%dT%H:%M:%S")
                    formatted_date = dt.strftime("%d/%m/%Y %H:%M")
                except Exception:
                    formatted_date = date_raw
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
    country_flags = {
        "United States": "🇺🇸",
        "Brazil": "🇧🇷",
        "Italy": "🇮🇹",
        "United Kingdom": "🇬🇧",
        "Mexico": "🇲🇽",
        "Spain": "🇪🇸",
        "Canada": "🇨🇦",
        "Australia": "🇦🇺",
        "France": "🇫🇷",
        "Germany": "🇩🇪",
        "Japan": "🇯🇵",
        "Austria": "🇦🇹",
        "Belgium": "🇧🇪",
        "Netherlands": "🇳🇱",
        "Hungary": "🇭🇺",
        "Saudi Arabia": "🇸🇦",
        "United Arab Emirates": "🇦🇪",
        "Singapore": "🇸🇬",
        "Monaco": "🇲🇨",
        "Qatar": "🇶🇦",
        "Azerbaijan": "🇦🇿",
        "China": "🇨🇳",
        "Bahrain": "🇧🇭"
    }
    circuit_urls = {
        "Las Vegas": "Las_Vegas",
        "Interlagos": "Brazil",
        "Mexico City": "Mexico",
        "Austin": "USA",
        "Singapore": "Singapore",
        "Baku": "Baku",
        "Monza": "Italy",
        "Zandvoort": "Netherlands",
        "Hungaroring": "Hungary",
        "Spa-Francorchamps": "Belgium",
        "Silverstone": "Great_Britain",
        "Spielberg": "Austria",
        "Montreal": "Canada",
        "Catalunya": "Spain",
        "Monte Carlo": "Monaco",
        "Imola": "Emilia_Romagna",
        "Miami": "Miami",
        "Jeddah": "Saudi_Arabia",
        "Suzuka": "Japan",
        "Sakhir": "Bahrain",
        "Shanghai": "China",
        "Melbourne": "Australia",
        "Yas Marina Circuit": "Abu_Dhabi",
        "Lusail": "Qatar"
    }
    items = filtered_items
    return render_template("races.html", items=items, col_tradotto=col_tradotto, country_flags=country_flags, circuit_urls=circuit_urls)
