from __future__ import annotations

from typing import Any, Dict, Optional

from flask import Blueprint, request, render_template, jsonify

from f1api.api import fetch_from_f1open

driver_bp = Blueprint("driver", __name__)

@driver_bp.route("/drivers/<driver_number>", methods=["GET"])
def driver_detail(driver_number: str):
    data = fetch_from_f1open(f"drivers/{driver_number}")

    if data.get("error"):
        return render_template("driver_detail.html", error=data.get("error"), driver={})

    return render_template("driver_detail.html", driver=data)