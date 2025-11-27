from __future__ import annotations

from typing import Dict, List
from flask import Blueprint, render_template

from f1api.api import fetch_from_f1open
from f1api.auth_decorators import login_required
from f1api.utils import get_team_logo_url, get_team_car_url

teams_bp = Blueprint("teams", __name__)


@teams_bp.route("/teams", methods=["GET"])
@login_required
def teams():
    """Pagina che mostra tutte le scuderie e i loro piloti."""
    
    # Recupera tutti i piloti dall'ultima sessione
    drivers_data = fetch_from_f1open("drivers?session_key=latest")
    drivers = drivers_data if isinstance(drivers_data, list) else []
    
    # Raggruppa i piloti per nome della scuderia
    teams_dict: Dict[str, List[dict]] = {}
    
    for driver in drivers:
        team_name = driver.get("team_name")
        if not team_name:
            continue
            
        if team_name not in teams_dict:
            teams_dict[team_name] = []
        
    # Aggiungi le informazioni del pilota alla scuderia
        teams_dict[team_name].append({
            "driver_number": driver.get("driver_number"),
            "full_name": driver.get("full_name"),
            "name_acronym": driver.get("name_acronym"),
            "headshot_url": driver.get("headshot_url") or "https://media.formula1.com/d_driver_fallback_image.png/content/",
            "team_colour": driver.get("team_colour")
        })
    
    # Converte il dict in una lista ordinata di scuderie
    teams_list = []
    for team_name, drivers_list in sorted(teams_dict.items()):
    # Prendi il colore della scuderia dal primo pilota (tutti i piloti della stessa scuderia condividono il colore)
        team_colour = drivers_list[0].get("team_colour") if drivers_list else None
        
        teams_list.append({
            "team_name": team_name,
            "team_colour": team_colour,
            "team_logo_url": get_team_logo_url(team_name),
            "team_car_url": get_team_car_url(team_name),
            "drivers": sorted(drivers_list, key=lambda d: d.get("driver_number") or 999)
        })
    
    return render_template(
        "teams.html",
        teams=teams_list
    )
