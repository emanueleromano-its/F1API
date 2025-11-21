from __future__ import annotations

from typing import Any, Dict, Optional

from flask import Blueprint, request, render_template, jsonify

from f1api.api import fetch_from_f1open

drivers_bp = Blueprint("drivers", __name__)


@drivers_bp.route("/drivers", methods=["GET"])
def drivers():
    q = request.args.get("search")
    params = {"search": q} if q else {}
    data = fetch_from_f1open("drivers?session_key=latest", params=params)

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
    exclude = {"meeting_key", "session_key", "broadcast_name", "country_code", "first_name", "last_name"}
    cols = []
    if items:
        first = items[0]
        if isinstance(first, dict):
            cols = [c for c in list(first.keys()) if c not in exclude]

    # Dedup items by 'broadcast_name' (preserve order)
    seen = set()
    unique_items = []
    for item in items:
        if not isinstance(item, dict):
            unique_items.append(item)
            continue
        key = item.get("broadcast_name")
        if item.get("headshot_url") is None:
            item["headshot_url"] = "https://media.formula1.com/d_driver_fallback_image.png/content/"
        if key is None:
            unique_items.append(item)
        elif key not in seen:
            seen.add(key)
            unique_items.append(item)

    unique_items = sorted(unique_items, key=lambda x: x.get("driver_number", ""))
    return render_template("drivers.html", items=unique_items, cols=cols)


@drivers_bp.route("/drivers/<driver_number>", methods=["GET"])
def driver_detail(driver_number: str):
    data = fetch_from_f1open(f"drivers?driver_number={driver_number}")
    return jsonify(data)
