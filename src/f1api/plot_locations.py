"""Scarica i dati di posizione dall'API OpenF1 e stampa/plotta le coordinate x,y.

Uso:
  - Per eseguire con dati reali passare l'URL completo via --url
  - Per testare localmente senza rete usare --sample

Esempio URL (dal tuo messaggio):
  https://api.openf1.org/v1/location?session_key=latest&driver_number=4&date%3E2025-11-09T17:00:00+00:00&date%3C2025-11-09T17:05:00+00:00

Il modulo stampa tutti i record ricevuti e apre una finestra con lo scatterplot
dei punti (x,y). Se non sono presenti coordinate, vengono ignorate.
"""
from __future__ import annotations

import argparse
import json
import sys
from typing import Any, Dict, List, Optional

import requests
import matplotlib.pyplot as plt


SAMPLE_DATA: List[Dict[str, Any]] = [
    {
        "date": "2025-11-09T17:01:02.322000+00:00",
        "session_key": 9869,
        "x": -2291,
        "z": 7567,
        "y": -2155,
        "meeting_key": 1273,
        "driver_number": 4,
    },
    {
        "date": "2025-11-09T17:01:12.500000+00:00",
        "session_key": 9869,
        "x": -2288,
        "z": 7568,
        "y": -2150,
        "meeting_key": 1273,
        "driver_number": 4,
    },
    {
        "date": "2025-11-09T17:01:22.900000+00:00",
        "session_key": 9869,
        "x": -2275,
        "z": 7570,
        "y": -2142,
        "meeting_key": 1273,
        "driver_number": 4,
    },
]


def fetch_json(url: str, timeout: float = 10.0) -> List[Dict[str, Any]]:
    """Recupera JSON dall'URL e restituisce una lista di record.

    Si assume che l'API ritorni un array JSON di oggetti. Se la risposta è un
    oggetto singolo che contiene una lista (es. {'data': [...]}) viene gestito
    in modo semplice provando a trovare la lista più ovvia.
    """
    resp = requests.get(url, timeout=timeout)
    resp.raise_for_status()
    payload = resp.json()

    # Se payload è già una lista -> ritorna come lista di record
    if isinstance(payload, list):
        return payload

    # Se è un dict, proviamo a trovare una lista al suo interno
    if isinstance(payload, dict):
        # common keys: 'data', 'results', 'locations'
        for key in ("data", "results", "locations"):
            if key in payload and isinstance(payload[key], list):
                return payload[key]
        # altrimenti: se ha valori che sono liste, usiamo la prima lista
        for v in payload.values():
            if isinstance(v, list):
                return v

    # Non siamo riusciti a normalizzare -> ritorniamo il payload avvolto in lista
    return [payload]


def extract_xy(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Estrae solo i campi rilevanti (x,y e il record originale come contesto).

    Restituisce una lista di dict con chiavi: x, y, index, raw
    """
    out: List[Dict[str, Any]] = []
    for i, r in enumerate(records):
        try:
            # alcuni dataset possono avere x/y come stringhe -> cast a float
            y = r.get("x")
            x = r.get("y")
            x = -x;
            if x is None or y is None:
                continue
            x_val = float(x)
            y_val = float(y)
        except (ValueError, TypeError):
            continue
        out.append({"index": i, "x": x_val, "y": y_val, "raw": r})
    return out


def print_records(records: List[Dict[str, Any]]) -> None:
    """Stampa a schermo tutti i record (formattato).

    Mostra anche le coordinate x,y per ogni record.
    """
    if not records:
        print("Nessun record da mostrare")
        return

    for i, r in enumerate(records):
        print(f"--- Record {i} ---")
        # stampiamo in formato json-friendly
        try:
            print(json.dumps(r, indent=2, ensure_ascii=False))
        except Exception:
            print(str(r))


def plot_xy(points: List[Dict[str, Any]], title: Optional[str] = None) -> None:
    """Mostra uno scatterplot dei punti x,y.

    Apre una finestra grafica che mostra i punti e li annota con l'indice.
    """
    if not points:
        print("Nessun punto xy da plottare")
        return

    xs = [p["x"] for p in points]
    ys = [p["y"] for p in points]

    fig, ax = plt.subplots(figsize=(8, 6))
    ax.scatter(xs, ys, c="tab:blue", s=40)
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    ax.set_title(title or "Location scatter (x vs y)")
    ax.grid(True, linestyle="--", alpha=0.5)

    # annotiamo con l'indice del punto (opzionale)
    for p in points:
        ax.annotate(str(p["index"]), (p["x"], p["y"]), textcoords="offset points", xytext=(4, 4), fontsize=8)

    # manteniamo rapporto di aspetto uguale per non deformare il piano cartesiano
    ax.set_aspect("equal", adjustable="datalim")
    plt.tight_layout()
    plt.show()


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Fetch and plot x/y locations from OpenF1 API")
    parser.add_argument("--url", help="URL completo dell'endpoint che ritorna i dati JSON", type=str)
    parser.add_argument("--sample", help="Usa dataset di esempio incorporato (no rete)", action="store_true")
    args = parser.parse_args(argv)

    records: List[Dict[str, Any]] = []
    if args.sample:
        records = SAMPLE_DATA
    elif args.url:
        try:
            records = fetch_json(args.url)
        except requests.RequestException as exc:
            print(f"Errore nella chiamata HTTP: {exc}")
            return 2
    else:
        parser.print_help()
        return 1

    # stampiamo i record originali
    print_records(records)

    # estraiamo x,y e plottiamo
    points = extract_xy(records)
    print(f"\nTrovati {len(points)} punti con coordinate x,y\n")
    plot_xy(points)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
