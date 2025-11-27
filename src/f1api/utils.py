"""Funzioni di utilità condivise tra le route."""
from __future__ import annotations

from datetime import datetime
from typing import Optional


def format_datetime(date_raw: Optional[str], fmt: str = "%d/%m/%Y %H:%M") -> Optional[str]:
    """Analizza e formatta stringhe datetime in formato ISO.

        Argomenti:
        date_raw: stringa datetime in formato ISO
        fmt: formato di output (default: dd/mm/YYYY HH:MM)

        Ritorna:
            Stringa formattata oppure il valore originale se il parsing fallisce
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
    """Restituisce una mappatura dei nomi dei paesi alle emoji delle bandiere."""
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
    """Restituisce una mappatura dei nomi brevi dei circuiti agli URL dei media F1."""
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
    """Costruisce l'URL dell'immagine del circuito a partire dal nome breve.

        Argomenti:
            circuit_short_name: nome breve come fornito dall'API (es. "Monza")

        Ritorna:
            URL completo all'immagine del circuito oppure stringa vuota se non trovato
    """
    if not circuit_short_name:
        return ""
    circuit_urls = get_circuit_urls()
    mapped_name = circuit_urls.get(circuit_short_name, "")
    if not mapped_name:
        return ""
    return f"https://media.formula1.com/image/upload/c_fit,h_704/q_auto/v1740000000/content/dam/fom-website/2018-redesign-assets/Circuit%20maps%2016x9/{mapped_name}_Circuit.webp"

def get_team_logo_url(team_name: Optional[str]) -> str:
    """Costruisce l'URL del logo della scuderia a partire dal nome della scuderia.

        Argomenti:
            team_name: nome della scuderia come fornito dall'API (es. "Mercedes")

        Ritorna:
            URL completo al logo della scuderia oppure stringa vuota se non trovato
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
    """Costruisce l'URL dell'immagine dell'auto della scuderia a partire dal nome.

        Argomenti:
            team_name: nome della scuderia come fornito dall'API (es. "Mercedes")

        Ritorna:
            URL completo all'immagine dell'auto della scuderia oppure stringa vuota se non trovato
    """
    if not team_name:
        return ""
    formatted_name = team_name.lower().replace(" ", "").replace(".", "").replace("&", "and")
    print(f"https://media.formula1.com/image/upload/c_lfill,w_3392/q_auto/v1740000000/common/f1/2025/{formatted_name}/2025{formatted_name}carright.webp")
    return f"https://media.formula1.com/image/upload/c_lfill,w_3392/q_auto/v1740000000/common/f1/2025/{formatted_name}/2025{formatted_name}carright.webp"