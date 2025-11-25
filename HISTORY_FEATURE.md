# 🔒 Protezione Pagine e Navigation History - Implementato

## ✅ Modifiche Completate

### 1. Protezione Route con Autenticazione

**Problema risolto**: Le pagine principali erano accessibili senza login.

**Route protette** (ora richiedono autenticazione):
- `/drivers` - Lista piloti
- `/driver/<number>` - Dettaglio pilota
- `/teams` - Lista team
- `/races` - Calendario gare

**Implementazione**:
```python
from f1api.auth_decorators import login_required

@app.route('/drivers')
@login_required
def drivers():
    # Solo utenti loggati possono accedere
    ...
```

### 2. Sistema di Tracking Navigazione

**Nuova funzionalità**: Salvataggio automatico della navigazione utente nel database.

#### Database Schema

Nuova tabella `page_history`:
```sql
CREATE TABLE page_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    page_url TEXT NOT NULL,
    page_title TEXT,
    visited_at TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
```

#### Tracking Automatico

**Middleware** in `app.py` che traccia automaticamente:
- ✅ Ogni pagina visitata (GET requests)
- ✅ Solo per utenti loggati (session attiva)
- ✅ URL della pagina
- ✅ Titolo della pagina
- ✅ Timestamp della visita

**Pagine escluse dal tracking**:
- `/static/*` - File statici
- `/api/*` - Endpoint API
- `/auth/*` - Pagine di autenticazione
- `/cache/*` - Endpoint cache

### 3. Nuova Route `/history`

**URL**: `http://localhost:5000/history`

**Funzionalità**:
- 📜 Visualizza cronologia completa della navigazione
- 📊 Statistiche: totale visite, pagine unique, ultima visita
- 🎨 Timeline visiva con icone per tipo di pagina
- 🔗 Link cliccabili per tornare alle pagine visitate
- 🗑️ Pulsante per cancellare tutta la history

**Protezione**: Richiede login (`@login_required`)

### 4. Nuova Route `/history/clear`

**Metodo**: POST  
**Funzionalità**: Cancella tutta la history dell'utente  
**Protezione**: Richiede login + conferma utente

---

## 📁 File Modificati

### 1. `src/f1api/auth_repository.py`
**Modifiche**:
- ➕ Creazione tabella `page_history`
- ➕ Metodo `track_page_visit(user_id, page_url, page_title)`
- ➕ Metodo `get_user_history(user_id, limit=50)`
- ➕ Metodo `clear_user_history(user_id)`

### 2. `src/f1api/app.py`
**Modifiche**:
- ➕ Middleware `@app.after_request` per tracking automatico
- ➕ Logic per mappare URL a titoli user-friendly
- ➕ Gestione errori per tracking (non fail request se tracking fallisce)

### 3. `src/f1api/routes/drivers.py`
**Modifiche**:
- ➕ Import `login_required`
- ➕ Decoratore `@login_required` su route `/drivers`

### 4. `src/f1api/routes/driver.py`
**Modifiche**:
- ➕ Import `login_required`
- ➕ Decoratore `@login_required` su route `/driver/<number>`

### 5. `src/f1api/routes/teams.py`
**Modifiche**:
- ➕ Import `login_required`
- ➕ Decoratore `@login_required` su route `/teams`

### 6. `src/f1api/routes/races.py`
**Modifiche**:
- ➕ Import `login_required`
- ➕ Decoratore `@login_required` su route `/races`

### 7. `src/f1api/routes/main.py`
**Modifiche**:
- ➕ Import `login_required`, `get_auth_repo`
- ➕ Route `/history` - visualizza cronologia
- ➕ Route `/history/clear` - cancella cronologia

### 8. `src/f1api/templates/base.html`
**Modifiche**:
- ➕ Link "History" nella navbar (solo per utenti loggati)

### 9. `src/f1api/templates/history.html` (NUOVO)
**Contenuto**:
- 📊 Dashboard statistiche (total visits, unique pages, last visit)
- 📜 Timeline cronologica con icone
- 🎨 Design responsive e coerente con tema F1
- 🗑️ Form per clear history
- 📭 Empty state per utenti senza history

---

## 🎯 Flusso Utente

### Scenario 1: Utente Non Loggato
1. Visita `/drivers` → **Redirect** a `/auth/login`
2. Flash message: "Please log in to access this page"
3. Dopo login → Redirect a `/drivers`

### Scenario 2: Utente Loggato
1. Login → Home page
2. Clicca "Drivers" → **Accesso consentito** + tracking automatico
3. Naviga "Teams", "Races", dettagli piloti → **Tutto tracciato**
4. Clicca "History" → Vede cronologia completa
5. (Opzionale) Clicca "Clear History" → Cancella tutto

---

## 🔍 Dettagli Tecnici

### Tracking Logic

```python
@app.after_request
def track_page_visit(response):
    if (response.status_code == 200 and 
        request.method == "GET" and 
        "user_id" in session):
        # Skip static/api/auth pages
        skip_paths = ["/static/", "/api", "/auth/", "/cache/"]
        if not any(request.path.startswith(path) for path in skip_paths):
            # Track visit
            auth_repo.track_page_visit(
                session["user_id"],
                request.path,
                page_title
            )
    return response
```

### Titoli Pagina

Mapping automatico URL → Titolo:
- `/` → "Home"
- `/drivers` → "Drivers List"
- `/teams` → "Teams"
- `/races` → "Races Calendar"
- `/driver/44` → "Driver #44"
- `/history` → "Navigation History"

### Icone Timeline

- 🏠 Home page
- 👤 Driver pages
- 🏆 Team pages
- 🏁 Race pages
- 📜 History page
- 📄 Other pages

---

## 📊 Esempi Query Database

### Visualizza history di un utente
```sql
SELECT page_url, page_title, visited_at
FROM page_history
WHERE user_id = 1
ORDER BY visited_at DESC
LIMIT 50;
```

### Conta visite per pagina
```sql
SELECT page_url, COUNT(*) as visits
FROM page_history
WHERE user_id = 1
GROUP BY page_url
ORDER BY visits DESC;
```

### Pagine più visitate (tutti gli utenti)
```sql
SELECT page_url, COUNT(*) as visits
FROM page_history
GROUP BY page_url
ORDER BY visits DESC
LIMIT 10;
```

---

## 🧪 Come Testare

### 1. Test Protezione Route

**Scenario**: Accesso senza login
```bash
# In una finestra privata/incognito
1. Vai su http://localhost:5000/drivers
2. Aspettati: redirect a /auth/login con messaggio flash
3. Stesso comportamento per /teams, /races, /driver/44
```

### 2. Test Tracking

**Scenario**: Navigazione con tracking
```bash
1. Login con un account
2. Visita: /drivers
3. Visita: /teams
4. Visita: /driver/1
5. Vai su /history
6. Aspettati: vedere tutte e 3 le visite registrate
```

### 3. Test Clear History

**Scenario**: Cancellazione history
```bash
1. Vai su /history
2. Clicca "Clear History"
3. Conferma l'alert
4. Aspettati: flash message "Successfully cleared X records"
5. Aspettati: empty state "No History Yet"
```

### 4. Test Icone

**Scenario**: Verifica icone corrette
```bash
1. Visita varie pagine
2. Vai su /history
3. Verifica icone:
   - 🏠 per home
   - 👤 per driver pages
   - 🏆 per teams
   - 🏁 per races
```

---

## 🎨 UI Features

### Statistiche Dashboard
- **Total Visits** - Numero totale di visite
- **Unique Pages** - Pagine unique visitate
- **Last Visit** - Data ultima visita

### Timeline
- Design card-based con hover effects
- Icone colorate per tipo pagina
- Link cliccabili per tornare alle pagine
- Timestamp formattato (YYYY-MM-DD HH:MM:SS)
- URL in monospace per leggibilità

### Empty State
- Messaggio friendly
- Link rapidi per iniziare a navigare
- Design coerente con resto app

---

## 🚀 Prossimi Passi (Opzionali)

### Possibili Miglioramenti

1. **Analytics Avanzati**
   - Pagine più visitate (chart)
   - Tempo medio per pagina
   - Pattern di navigazione

2. **Filtri History**
   - Per data range
   - Per tipo di pagina
   - Ricerca full-text

3. **Export History**
   - Download CSV
   - Download JSON
   - Email report

4. **Limit History**
   - Auto-delete dopo X giorni
   - Limite massimo record per utente
   - Compressione history vecchia

5. **Privacy**
   - Opzione "Don't track me"
   - Incognito mode
   - Auto-clear on logout

---

## ✅ Checklist Completamento

- [x] Protezione route `/drivers` con `@login_required`
- [x] Protezione route `/driver/<number>` con `@login_required`
- [x] Protezione route `/teams` con `@login_required`
- [x] Protezione route `/races` con `@login_required`
- [x] Creazione tabella `page_history` nel database
- [x] Middleware tracking automatico in `app.py`
- [x] Metodi repository: `track_page_visit`, `get_user_history`, `clear_user_history`
- [x] Route `/history` per visualizzare cronologia
- [x] Route `/history/clear` per cancellare cronologia
- [x] Template `history.html` con timeline e statistiche
- [x] Link "History" nella navbar
- [x] Flash messages per feedback utente
- [x] Design responsive per mobile
- [x] Gestione empty state
- [x] Conferma prima di clear history

---

## 🎉 Risultato Finale

**Ora l'applicazione**:
1. ✅ Richiede login per accedere alle pagine principali
2. ✅ Traccia automaticamente la navigazione di ogni utente
3. ✅ Mostra cronologia in una pagina dedicata con statistiche
4. ✅ Permette di cancellare la cronologia
5. ✅ Mantiene un'esperienza utente fluida e sicura

**Pronto per il test!** 🏎️
