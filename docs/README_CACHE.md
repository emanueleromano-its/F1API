# F1API - Cache Implementation Guide

## Quick Start

### 1. Install Dependencies

```bash
# Create virtual environment
python -m venv .venv

# Activate (Windows PowerShell)
.\.venv\Scripts\Activate.ps1

# Install packages
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
# Copy example configuration
cp .env.example .env

# Edit .env with your settings
# Key settings:
# - CACHE_DB_PATH: Where to store cache database
# - CACHE_TTL_SECONDS: How long to cache responses
```

### 3. Run Application

```bash
python src/f1api/app.py
```

Application will be available at `http://localhost:5000`

### 4. Verify Cache is Working

```bash
# Get cache statistics
curl http://localhost:5000/cache/stats

# Make a request (first time - cache miss)
curl http://localhost:5000/drivers

# Make same request again (cache hit - no API call)
curl http://localhost:5000/drivers

# Check stats again to see cache entry
curl http://localhost:5000/cache/stats
```

## Cache System Overview

L'applicazione utilizza un sistema di **cache persistente basato su SQLite** per:

- Ridurre la latenza per le richieste ripetute
- Minimizzare il carico sull'API esterna F1 Open
- Fornire un fallback quando l'API non è disponibile
- Supportare richieste condizionali (ETag) per risparmiare banda

### Caratteristiche Principali

✅ **Cache persistente** - Sopravvive ai riavvii dell'app  
✅ **Scadenza basata su TTL** - Durata della cache configurabile  
✅ **Supporto ETag** - Richieste condizionali efficienti  
✅ **Fallback dati obsoleti** - Serve dati cache quando l'API fallisce  
✅ **Thread-safe** - Gestisce richieste concorrenti  
✅ **Endpoint di gestione** - Pulisce/rimuove cache via API  

## Architettura

```text
Request → fetch_from_f1open() → CacheRepository
                                      ↓
                              Check cache (valid?)
                                 ↙         ↘
                            Cache HIT   Cache MISS
                                ↓           ↓
                         Return cached   Call API
                             data            ↓
                                        Save to cache
                                             ↓
                                        Return data
```

See [docs/CACHE.md](docs/CACHE.md) for detailed architecture documentation.

## Configurazione

### Variabili d'Ambiente

| Variabile | Default | Descrizione |
|----------|---------|-------------|
| `CACHE_DB_PATH` | `./data/cache.db` | Percorso al database SQLite |
| `CACHE_TTL_SECONDS` | `300` | TTL di default per la cache (5 minuti) |
| `F1OPEN_API_BASE` | `https://api.openf1.org/v1` | URL base API F1 Open |
| `PORT` | `5000` | Porta del server Flask |

### Cache TTL Guidelines

- **Live race data**: 30-60 seconds
- **Session data**: 300 seconds (5 minutes)
- **Historical data**: 3600 seconds (1 hour)
- **Driver/team info**: 86400 seconds (1 day)

## API Endpoints

### Data Endpoints (Cached)

| Endpoint | Description | Cache TTL |
|----------|-------------|-----------|
| `GET /drivers` | Elenca tutti i piloti | Default |
| `GET /races` | Elenca gare/sessioni | Default |
| `GET /position` | Posizioni in gara | Default |

Tutti gli endpoint dati utilizzano automaticamente la cache quando disponibile.

### Endpoint di Gestione Cache

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/cache/stats` | GET | Ottieni statistiche della cache |
| `/cache/clear` | POST | Pulisci tutta la cache o URL specifico |
| `/cache/cleanup` | POST | Rimuovi voci scadute |

#### Esempi

**Ottieni statistiche della cache:**

```bash
curl http://localhost:5000/cache/stats
```

Response:

```json
{
  "total_entries": 15,
  "expired_entries": 2,
  "valid_entries": 13,
  "db_size_bytes": 524288,
  "db_path": "./data/cache.db"
}
```

**Pulisci tutta la cache:**

```bash
curl -X POST http://localhost:5000/cache/clear
```

**Pulisci URL specifico:**

```bash
curl -X POST "http://localhost:5000/cache/clear?url=https://api.openf1.org/v1/drivers"
```

**Pulisci voci scadute:**

```bash
curl -X POST http://localhost:5000/cache/cleanup
```

## Risoluzione Problemi

### Cache non funziona (fa sempre chiamate API)

**Controlla:**

1. Verifica le statistiche della cache: `curl http://localhost:5000/cache/stats`
2. Controlla che il TTL non sia troppo basso: `echo $CACHE_TTL_SECONDS`
3. Verifica che il percorso del database sia scrivibile

**Soluzione:**

```bash
export CACHE_TTL_SECONDS=600
export CACHE_DB_PATH=/writable/path/cache.db
```

### Database locked errors

SQLite ha una concorrenza limitata. Per scenari ad alto traffico:

- Considera Redis o Memcached
- Aumenta il timeout di SQLite
- Usa il connection pooling

### Cache troppo grande

```bash
# Controlla la dimensione attuale
curl http://localhost:5000/cache/stats

# Rimuovi le voci scadute
curl -X POST http://localhost:5000/cache/cleanup

# Pulisci tutta la cache se necessario
curl -X POST http://localhost:5000/cache/clear
```

### Aggiunta di nuovi endpoint con cache

Tutti gli endpoint che utilizzano `fetch_from_f1open()` sono automaticamente memorizzati nella cache:

```python
from f1api.api import fetch_from_f1open

@app.route("/teams")
def teams():
    # Automatically cached!
    data = fetch_from_f1open("teams")
    return jsonify(data)
```

To force refresh (bypass cache):

```python
data = fetch_from_f1open("teams", force_refresh=True)
```

## Deployment in Produzione

### Raccomandazioni

1. **Usa un server WSGI di produzione:**

   ```bash
   pip install gunicorn
   gunicorn -w 4 -b 0.0.0.0:5000 "f1api.app:create_app()"
   ```

2. **Imposta un TTL più lungo per i dati stabili:**

   ```bash
   export CACHE_TTL_SECONDS=3600
   ```

3. **Usa un percorso assoluto per il database della cache:**

   ```bash
   export CACHE_DB_PATH=/var/lib/f1api/cache.db
   ```

4. **Configura la pulizia programmata della cache:**

   ```bash
   # Cron job ogni ora
   0 * * * * curl -X POST http://localhost:5000/cache/cleanup
   ```

5. **Monitor cache hit rate:**
   - Add logging/metrics for cache performance
   - Track cache hit/miss ratio
   - Alert on high miss rates
