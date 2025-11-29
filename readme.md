# F1API

## Breve descrizione
-----------------
`F1API` è un'app Flask per esplorare dati di Formula 1 ottenuti dall'API pubblica F1Open. Fornisce pagine per visualizzare piloti, gare, sessioni e classifiche.

## Caratteristiche principali

-------------------------;

- Liste e dettagli di piloti (`/drivers`, `/driver/<id>`).
- Elenco gare e dettaglio meeting (`/races`, `/race/<meeting_key>`).
- Classifiche sessioni (session results) e dettaglio pilota (laps, pit stops).

## Prerequisiti

------------;

- Python 3.10+ (3.12 consigliato)
- Virtual environment (`venv`)

## Installazione (PowerShell - Windows)

-----------------------------------;

Apri PowerShell nella root del progetto e segui questi passi:

1; Crea e attiva la venv:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2; Aggiorna `pip` e installa le dipendenze:

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Opzione per sviluppo (editable):

```powershell
pip install -e .
```

## Esecuzione

----------;

Per avviare l'app:

- Avvio rapido tramite wrapper che aggiunge `src/` al `PYTHONPATH`:

```powershell
python run.py
```

- Se hai eseguito `pip install -e .` puoi usare direttamente:

```powershell
python -m f1api.app
```

Variabili d'ambiente e `.env`

-----------------------------;

- Per sviluppo puoi creare un file `.env` nella root con le variabili locali. Assicurati di non commitare segreti.
- VSCode può caricare automaticamente il file `.env` se configurato.

## Struttura rilevante del progetto

-------------------------------;

- `src/f1api/`
	- `app.py` — factory Flask e registrazione blueprint
	- `api.py` — wrapper per chiamate all'API esterna
	- `routes/` — blueprint (drivers, races, race, driver, main)
	- `templates/` — Jinja2 templates (usano `base.html`)
	- `static/` — CSS e fonts (posiziona font in `static/fonts/`)
	- `utils.py` — funzioni riutilizzabili (date, immagini circuiti…)
