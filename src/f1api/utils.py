"""Utility functions shared across routes."""
from __future__ import annotations

from datetime import datetime
from typing import Optional


def format_datetime(date_raw: Optional[str], fmt: str = "%d/%m/%Y %H:%M") -> Optional[str]:
    """Parse and format ISO datetime strings.
    
    Args:
        date_raw: ISO format datetime string
        fmt: Output format (default: dd/mm/yyyy hh:mm)
    
    Returns:
        Formatted string or original value if parsing fails
    """
    if not date_raw:
        return None
    try:
        dt = datetime.fromisoformat(date_raw)
        return dt.strftime(fmt)
    except Exception:
        try:
            # fallback if timezone-less ISO
            dt = datetime.strptime(date_raw, "%Y-%m-%dT%H:%M:%S")
            return dt.strftime(fmt)
        except Exception:
            return date_raw


def get_country_flags() -> dict[str, str]:
    """Returns mapping of country names to flag emojis."""
    return {
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


def get_circuit_urls() -> dict[str, str]:
    """Returns mapping of circuit short names to F1 media URLs."""
    return {
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


def get_circuit_image_url(circuit_short_name: Optional[str]) -> str:
    """Build F1 circuit image URL from circuit short name.
    
    Args:
        circuit_short_name: Short name from API (e.g. "Monza")
    
    Returns:
        Full URL to circuit image or empty string if not found
    """
    if not circuit_short_name:
        return ""
    circuit_urls = get_circuit_urls()
    mapped_name = circuit_urls.get(circuit_short_name, "")
    if not mapped_name:
        return ""
    return f"https://media.formula1.com/image/upload/c_fit,h_704/q_auto/v1740000000/content/dam/fom-website/2018-redesign-assets/Circuit%20maps%2016x9/{mapped_name}_Circuit.webp"

def get_team_logo_url(team_name: Optional[str]) -> str:
    """Build F1 team logo image URL from team name.
    
    Args:
        team_name: Name of the team from API (e.g. "Mercedes")
    
    Returns:
        Full URL to team logo image or empty string if not found
    """
    if not team_name:
        return ""
    formatted_name = team_name.lower().replace(" ", "").replace(".", "").replace("&", "and")
    print(f"https://media.formula1.com/image/upload/c_fit,h_64/q_auto/v1740000000/common/f1/2025/{formatted_name}/2025{formatted_name}logo.webp")
    if formatted_name == "mercedes" or formatted_name == "astonmartin":
        return f"https://media.formula1.com/image/upload/c_fit,h_64/q_auto/v1740000000/common/f1/2025/{formatted_name}/2025{formatted_name}logolight.webp"
    else:
        return f"https://media.formula1.com/image/upload/c_fit,h_64/q_auto/v1740000000/common/f1/2025/{formatted_name}/2025{formatted_name}logo.webp"

def get_team_car_url(team_name: Optional[str]) -> str:
    """Build F1 team car image URL from team name.
    
    Args:
        team_name: Name of the team from API (e.g. "Mercedes")
    
    Returns:
        Full URL to team car image or empty string if not found
    """
    if not team_name:
        return ""
    formatted_name = team_name.lower().replace(" ", "").replace(".", "").replace("&", "and")
    print(f"https://media.formula1.com/image/upload/c_lfill,w_3392/q_auto/v1740000000/common/f1/2025/{formatted_name}/2025{formatted_name}carright.webp")
    return f"https://media.formula1.com/image/upload/c_lfill,w_3392/q_auto/v1740000000/common/f1/2025/{formatted_name}/2025{formatted_name}carright.webp"