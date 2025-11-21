"""Run helper: aggiunge `src/` al `sys.path` e avvia l'app in sviluppo.

Questo permette di eseguire l'app con il comando:
    python run.py

Alternativa (consigliata per ambienti ripetibili):
    - Impostare `PYTHONPATH=src` e lanciare `python -m f1api.app`
    - Oppure installare in editable mode: `pip install -e .`
"""
from __future__ import annotations

import os
import sys

# Aggiungi la cartella `src` al percorso dei moduli, in modo che
# `import f1api` funzioni indipendentemente dalla cwd di esecuzione.
ROOT = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(ROOT, "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from f1api.app import create_app


def main() -> None:
    app = create_app()
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)), debug=True)


if __name__ == "__main__":
    main()
