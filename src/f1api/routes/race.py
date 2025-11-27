from __future__ import annotations

from typing import Any, Dict, Optional, List

from flask import Blueprint, request, render_template

from f1api.api import fetch_from_f1open
from f1api.utils import format_datetime, get_country_flags, get_circuit_image_url

race_bp = Blueprint("race", __name__)


@race_bp.route("/race/<meeting_key>", methods=["GET"])
def race_detail(meeting_key: str):
    """Pagina dettaglio race meeting con info circuito e classifiche per ogni sessione.
    
    Argomenti:
        meeting_key: chiave del meeting (es. "1234" o "latest")
    """
    # 1. Fetch meeting info
    meeting_info = None
    meeting_data = fetch_from_f1open(f"meetings?meeting_key={meeting_key}")
    if isinstance(meeting_data, list) and len(meeting_data) > 0:
        meeting_info = meeting_data[0]
        # Format date_start
        if meeting_info.get("date_start"):
            meeting_info["date_start_formatted"] = format_datetime(meeting_info["date_start"])
        # Get circuit image URL
        circuit_short = meeting_info.get("circuit_short_name")
        meeting_info["circuit_image_url"] = get_circuit_image_url(circuit_short)
    
    # 2. Fetch all sessions for this meeting
    sessions_data = fetch_from_f1open(f"sessions?meeting_key={meeting_key}")
    sessions = sessions_data if isinstance(sessions_data, list) else []
    
    # Sort sessions by date_start
    sessions = sorted(sessions, key=lambda s: s.get("date_start", ""))
    
    # 3. For each session, fetch session results and driver data
    session_results_map = {}
    for session in sessions:
        session_key = session.get("session_key")
        session_name = session.get("session_name") or session.get("session_type", "Unknown")
        if not session_key:
            continue
        
        # Fetch session results
        results_data = fetch_from_f1open(f"session_result?session_key={session_key}")
        results = results_data if isinstance(results_data, list) else []
        
        # Fetch driver data for this session
        drivers_data = fetch_from_f1open(f"drivers?session_key={session_key}")
        drivers = drivers_data if isinstance(drivers_data, list) else []
        
        # Build driver lookup map by driver_number
        driver_map = {}
        for driver in drivers:
            driver_num = driver.get("driver_number")
            if driver_num:
                driver_map[driver_num] = driver
        
        # Sort by position (handle None/DNF cases)
        results = sorted(results, key=lambda r: r.get("position") if r.get("position") else 999)
        
        # Enrich results with driver data and computed fields
        for idx, result in enumerate(results):
            driver_num = result.get("driver_number")
            
            # Merge driver data if available
            if driver_num and driver_num in driver_map:
                driver_info = driver_map[driver_num]
                result["full_name"] = driver_info.get("full_name") or result.get("full_name")
                result["name_acronym"] = driver_info.get("name_acronym") or result.get("name_acronym")
                result["team_name"] = driver_info.get("team_name") or result.get("team_name")
                result["team_colour"] = driver_info.get("team_colour")
            
            # Add rank for display
            result["display_position"] = result.get("position") or "DNF"
            
            # Compute gap to leader (if available)
            if idx == 0:
                result["gap_to_leader"] = "Leader"
            
            # Status formatting
            status = []
            if result.get("dnf"):
                status.append("DNF")
            if result.get("dns"):
                status.append("DNS")
            if result.get("dsq"):
                status.append("DSQ")
            result["status_display"] = ", ".join(status) if status else "Finished"
        
        session_results_map[session_key] = {
            "session_name": session_name,
            "session_type": session.get("session_type"),
            "date_start": format_datetime(session.get("date_start")),
            "results": results
        }
    
    # 4. Fetch all meetings for dropdown selector
    meetings_data = fetch_from_f1open("meetings")
    meetings = meetings_data if isinstance(meetings_data, list) else []
    meetings = sorted(meetings, key=lambda m: m.get("date_start", ""), reverse=True)
    
    return render_template(
        "race-detail.html",
        meeting_info=meeting_info,
        meeting_key=meeting_key,
        sessions=sessions,
        session_results_map=session_results_map,
        meetings=meetings,
        country_flags=get_country_flags()
    )
