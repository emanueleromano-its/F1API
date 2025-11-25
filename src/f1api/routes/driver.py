from __future__ import annotations

from typing import Any, Dict, Optional

from flask import Blueprint, request, render_template, jsonify

from f1api.api import fetch_from_f1open
from f1api.auth_decorators import login_required
from f1api.utils import format_datetime, get_country_flags, get_circuit_image_url

driver_bp = Blueprint("driver", __name__)


@driver_bp.route("/driver/<driver_number>", methods=["GET"])
@login_required
def driver_detail(driver_number: str):
    """Pagina dettaglio pilota con info, risultati, laps e pit stops.
    
    Query params opzionali:
    - meeting_key: filtro per race week (default: latest)
    - session_key: filtro per sessione (default: latest)
    """
    # Get filters from query params
    meeting_key = request.args.get("meeting_key", "latest")
    session_key = request.args.get("session_key", "latest")
    
    # 1. Fetch driver info (per header)
    driver_data = fetch_from_f1open(f"drivers?driver_number={driver_number}&session_key=latest")
    driver_info = None
    if isinstance(driver_data, list) and len(driver_data) > 0:
        driver_info = driver_data[0]
    elif isinstance(driver_data, dict) and not driver_data.get("error"):
        driver_info = driver_data
    
    # Fallback headshot
    if driver_info and not driver_info.get("headshot_url"):
        driver_info["headshot_url"] = "https://media.formula1.com/d_driver_fallback_image.png/content/"
    
    # 2. Fetch session results
    session_result_data = fetch_from_f1open(
        f"session_result?driver_number={driver_number}&meeting_key={meeting_key}"
    )
    session_results = session_result_data if isinstance(session_result_data, list) else []
    
    # 3. Fetch laps
    laps_data = fetch_from_f1open(
        f"laps?driver_number={driver_number}&session_key={session_key}"
    )
    laps = laps_data if isinstance(laps_data, list) else []
    # 3b. Attempt to fetch stints so we can map laps to tyre compounds when
    # lap-level tyre data (lap.tyre_compound) is missing. Build a simple
    # lap -> compound map: { lap_number: compound }
    lap_compound_map: Dict[int, str] = {}
    try:
        stints_data = fetch_from_f1open(
            f"stints?driver_number={driver_number}&session_key={session_key}"
        )
        if isinstance(stints_data, list):
            for stint in stints_data:
                compound = stint.get("compound")
                # start_lap / end_lap may be strings or ints
                start = stint.get("lap_start")
                end = stint.get("lap_end")
                if compound and start is not None and end is not None:
                    try:
                        start_i = int(start)
                        end_i = int(end)
                    except Exception:
                        continue
                    for lap_n in range(start_i, end_i + 1):
                        # Only set if not already present (earlier stints take precedence)
                        if lap_n not in lap_compound_map:
                            lap_compound_map[lap_n] = compound
                            # also store string key so template lookups succeed if lap numbers are strings
                            lap_compound_map[str(lap_n)] = compound
    except Exception:
        # Don't fail the whole page if stints endpoint is unavailable
        lap_compound_map = {}
    
    # 4. Fetch pit stops
    pit_data = fetch_from_f1open(
        f"pit?driver_number={driver_number}&session_key={session_key}"
    )
    pit_stops = pit_data if isinstance(pit_data, list) else []
    # Convert pit stop date strings to datetime objects for better formatting in template
    from datetime import datetime
    for pit in pit_stops:
        date_str = pit.get("date")
        if date_str:
            try:
                pit["date"] = datetime.fromisoformat(date_str)
            except Exception:
                try:
                    pit["date"] = datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%S")
                except Exception:
                    pit["date"] = None
        else:
            pit["date"] = None
    
    # 5. Fetch available meetings per dropdown (ultimi 5)
    meetings_data = fetch_from_f1open("meetings")
    meetings = meetings_data if isinstance(meetings_data, list) else []
    
    # 6. Fetch available sessions per dropdown (per il meeting corrente)
    sessions_data = fetch_from_f1open(f"sessions?meeting_key={meeting_key}")
    sessions = sessions_data if isinstance(sessions_data, list) else []
    # Build a mapping session_key -> session_name (or session_type) for template lookup
    session_map = {}
    for s in sessions:
        try:
            key = s.get("session_key")
            name = s.get("session_name") or s.get("session_type") or s.get("name")
            if key and name:
                session_map[key] = name
        except Exception:
            continue
    
    # 7. Fetch meeting info for display
    meeting_info = None
    if meeting_key and meeting_key != "latest":
        meeting_data = fetch_from_f1open(f"meetings?meeting_key={meeting_key}")
        if isinstance(meeting_data, list) and len(meeting_data) > 0:
            meeting_info = meeting_data[0]
            # Format date_start
            if meeting_info.get("date_start"):
                meeting_info["date_start_formatted"] = format_datetime(meeting_info["date_start"])
            # Get circuit image URL
            circuit_short = meeting_info.get("circuit_short_name")
            meeting_info["circuit_image_url"] = get_circuit_image_url(circuit_short)
    
    return render_template(
        "driver-detail.html",
        driver=driver_info,
        driver_number=driver_number,
        session_results=session_results,
        laps=laps,
        lap_compound_map=lap_compound_map,
        pit_stops=pit_stops,
        meetings=meetings,
        sessions=sessions,
        current_meeting=meeting_key,
        current_session=session_key,
        session_map=session_map,
        meeting_info=meeting_info,
        country_flags=get_country_flags()
    )