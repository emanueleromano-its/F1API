# Cache Architecture Documentation

## Overview

L'applicazione F1API implementa un sistema di cache persistente basato su SQLite per ottimizzare le chiamate all'API esterna F1Open. Questo documento descrive l'architettura, l'utilizzo e il troubleshooting del sistema di caching.

## Architettura

### Componenti principali

1. **CacheRepository** (`src/f1api/cache_repository.py`)
   - Layer di accesso al database SQLite
   - Gestisce operazioni CRUD sulla cache
   - Thread-safe per gestire richieste concorrenti
   - Supporta TTL (Time-To-Live) configurabile
   - Implementa conditional requests con ETag

2. **fetch_from_f1open** (`src/f1api/api.py`)
   - Wrapper HTTP centralizzato per chiamate API
   - Integra la cache in modo trasparente
   - Gestisce fallback su cache stale in caso di errori API
   - Supporta force refresh

3. **Cache Management Endpoints** (`src/f1api/routes/main.py`)
   - `/cache/stats` - Statistiche cache
   - `/cache/clear` - Invalidazione cache
   - `/cache/cleanup` - Rimozione entry scadute

### Schema Database

```sql
CREATE TABLE api_cache (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    resource_key TEXT UNIQUE NOT NULL,     -- SHA256(url + params)
    response_body TEXT NOT NULL,            -- JSON serializzato
    status_code INTEGER NOT NULL,
    headers TEXT,                           -- JSON headers HTTP
    created_at TEXT NOT NULL,               -- ISO 8601 timestamp
    updated_at TEXT NOT NULL,               -- ISO 8601 timestamp
    expires_at TEXT,                        -- ISO 8601 timestamp (TTL)
    etag TEXT                               -- ETag per conditional requests
);

CREATE INDEX idx_resource_key ON api_cache(resource_key);
CREATE INDEX idx_expires_at ON api_cache(expires_at);
```

### Flusso di Richiesta

```
┌─────────────────────────────────────────────────────────────┐
│ 1. HTTP Request (es. GET /drivers)                          │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. fetch_from_f1open(path, params)                          │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. CacheRepository.get(url, params)                         │
│    - Calcola resource_key = SHA256(url + params)            │
│    - Query: SELECT * WHERE resource_key = ? AND not expired │
└────────────┬───────────────────────────┬────────────────────┘
             │                           │
        Cache HIT                   Cache MISS
             │                           │
             ▼                           ▼
    ┌────────────────┐      ┌─────────────────────────────────┐
    │ Return cached  │      │ 4. Prepara headers con ETag     │
    │ response       │      │    (If-None-Match da cache stale)│
    └────────────────┘      └──────────┬──────────────────────┘
                                       │
                                       ▼
                         ┌─────────────────────────────────────┐
                         │ 5. requests.get(url, headers)       │
                         └──────────┬──────────────────────────┘
                                    │
                    ┌───────────────┴───────────────┐
                    │                               │
              Status 304                      Status 200
           (Not Modified)                  (New data)
                    │                               │
                    ▼                               ▼
    ┌────────────────────────────┐   ┌─────────────────────────┐
    │ 6a. Riusa body da cache    │   │ 6b. Salva nuovi dati    │
    │     Aggiorna solo TTL      │   │     in cache            │
    └────────────────────────────┘   └─────────────────────────┘
                    │                               │
                    └───────────────┬───────────────┘
                                    │
                                    ▼
                         ┌─────────────────────────┐
                         │ 7. Return response      │
                         └─────────────────────────┘
                                    │
                                    ▼
                    ┌───────────────────────────────┐
                    │ Error? → Fallback cache stale │
                    └───────────────────────────────┘
```

## Configurazione

### Variabili d'Ambiente

```bash
# Path del database SQLite (default: ./data/cache.db)
CACHE_DB_PATH=/path/to/cache.db

# TTL default in secondi (default: 300 = 5 minuti)
CACHE_TTL_SECONDS=600

# Base URL dell'API F1Open (default: https://api.openf1.org/v1)
F1OPEN_API_BASE=https://api.openf1.org/v1
```

### Esempio .env

```bash
CACHE_DB_PATH=./data/f1_cache.db
CACHE_TTL_SECONDS=300
F1OPEN_API_BASE=https://api.openf1.org/v1
PORT=5000
```

## Politiche di Caching

### TTL (Time-To-Live)

- **Default**: 300 secondi (5 minuti)
- Configurabile tramite `CACHE_TTL_SECONDS`
- Calcolato al momento del salvataggio: `expires_at = now + TTL`
- Le richieste dopo `expires_at` non usano la cache e richiamano l'API

### Conditional Requests (ETag)

Se l'API supporta ETag:
1. Alla prima richiesta, l'ETag viene salvato nella cache
2. Quando la cache scade, viene inviato `If-None-Match: <etag>`
3. Se l'API risponde **304 Not Modified**:
   - Il body non cambia (riusato da cache)
   - Solo metadata (TTL) viene aggiornato
   - Risparmio di bandwidth

### Fallback su Errori API

Se la chiamata API fallisce (timeout, 500, network error):
1. Verifica se esiste una voce in cache (anche scaduta)
2. Se esiste, ritorna i dati stale con warning:
   ```json
   {
     "data": [...],
     "_cache_warning": "Using stale cached data due to API error",
     "_api_error": "Connection timeout"
   }
   ```
3. Se non esiste cache, ritorna errore standard

### Force Refresh

Per bypassare la cache:
```python
from f1api.api import fetch_from_f1open

data = fetch_from_f1open("drivers", force_refresh=True)
```

## API Endpoints per Cache Management

### GET /cache/stats

Statistiche cache corrente.

**Response:**
```json
{
  "total_entries": 42,
  "expired_entries": 5,
  "valid_entries": 37,
  "db_size_bytes": 1048576,
  "db_path": "./data/cache.db"
}
```

### POST /cache/clear

Invalida tutta la cache o una risorsa specifica.

**Clear all:**
```bash
curl -X POST http://localhost:5000/cache/clear
```

**Clear specific URL:**
```bash
curl -X POST "http://localhost:5000/cache/clear?url=https://api.openf1.org/v1/drivers"
```

**Response:**
```json
{
  "message": "Cleared all cache (42 entries)"
}
```

### POST /cache/cleanup

Rimuove solo le entry scadute (garbage collection).

```bash
curl -X POST http://localhost:5000/cache/cleanup
```

**Response:**
```json
{
  "message": "Removed 5 expired entries"
}
```

## Thread Safety e Concorrenza

### Gestione Race Conditions

- **SQLite locking**: Usa `INSERT ... ON CONFLICT DO UPDATE` per upsert atomico
- **Thread-local connections**: Ogni thread ha la propria connessione DB
- **Global lock**: Lock Python per operazioni critiche (write, invalidate)

### Scenario: Due richieste parallele per la stessa risorsa

1. Thread A e Thread B richiedono `/drivers` contemporaneamente
2. Entrambi rilevano cache miss
3. Entrambi chiamano l'API
4. L'upsert SQLite garantisce che solo l'ultima write vinca
5. Nessuna corruzione dati

## Testing

### Unit Tests

```bash
# Esegui test cache repository
pytest tests/test_cache.py -v

# Con coverage
pytest tests/test_cache.py --cov=f1api.cache_repository --cov-report=html
```

### Integration Tests

```bash
# Esegui test integrazione Flask
pytest tests/test_cache_integration.py -v
```

### Test Coverage

Copertura richiesta: >80%

- [x] Cache hit/miss
- [x] TTL expiration
- [x] Stale fallback
- [x] Invalidation (all/specific)
- [x] ETag conditional requests
- [x] Thread safety
- [x] Stats endpoint
- [x] Error handling

## Troubleshooting

### Cache non funziona (sempre chiamate API)

**Causa possibile**: TTL troppo basso o cache non inizializzata

**Debug:**
```bash
# Verifica stats
curl http://localhost:5000/cache/stats

# Controlla log
# Aggiungi logging in fetch_from_f1open per vedere se get() ritorna None
```

**Soluzione:**
```bash
# Aumenta TTL
export CACHE_TTL_SECONDS=600

# Verifica path DB sia writable
export CACHE_DB_PATH=/writable/path/cache.db
```

### Database locked errors

**Causa**: Troppe connessioni concorrenti o timeout breve

**Soluzione:**
- SQLite ha un `busy_timeout` default basso
- Considera connection pooling o passa a PostgreSQL per workload molto concorrenti

### Cache troppo grande

**Causa**: Troppe entry non scadute

**Soluzione:**
```bash
# Pulizia manuale delle scadute
curl -X POST http://localhost:5000/cache/cleanup

# Clear completo
curl -X POST http://localhost:5000/cache/clear

# Riduci TTL per risorse dinamiche
export CACHE_TTL_SECONDS=60
```

### ETag non utilizzato

**Causa**: L'API F1Open potrebbe non restituire header `ETag`

**Verifica:**
```bash
curl -I https://api.openf1.org/v1/drivers
```

**Nota**: Se l'API non supporta ETag, il sistema continua a funzionare normalmente usando solo TTL.

## Performance Considerations

### Vantaggi

- **Riduzione latenza**: Cache hit ~1-5ms vs API call ~100-500ms
- **Riduzione carico**: Meno richieste all'API esterna
- **Resilienza**: Fallback su cache stale se API down
- **Bandwidth**: Conditional requests (304) risparmiano dati

### Limiti

- **SQLite**: Performance degrada con >100k entry o alta concorrenza
- **Disk I/O**: Letture/scritture sincrone (considera async per scale)
- **Stale data**: Utente potrebbe vedere dati non aggiornati entro TTL

### Raccomandazioni Produzione

1. **Monitoring**: Aggiungi metriche (cache hit rate, avg response time)
2. **Backup**: Pianifica backup periodici del DB cache
3. **Cleanup**: Scheduled job per `cleanup_expired()` ogni ora
4. **Scale**: Per >1000 req/sec, considera Redis o Memcached

## Migration Path

Per future modifiche dello schema:

1. Crea script di migrazione in `migrations/`
2. Usa libreria come `alembic` (se adotti ORM) o SQL raw
3. Implementa versioning dello schema (es. `PRAGMA user_version`)

**Esempio migrazione:**
```sql
-- migrations/001_add_compression.sql
ALTER TABLE api_cache ADD COLUMN compressed BOOLEAN DEFAULT 0;
ALTER TABLE api_cache ADD COLUMN compression_algo TEXT;
```

## Conclusioni

Il sistema di cache implementato fornisce:
- ✅ Persistenza SQLite con schema robusto
- ✅ TTL configurabile
- ✅ ETag support per conditional requests
- ✅ Fallback stale su errori
- ✅ Thread safety
- ✅ Endpoints di management
- ✅ Test automatici completi

Per domande o issue, consulta il team di sviluppo o apri un ticket su GitHub.
