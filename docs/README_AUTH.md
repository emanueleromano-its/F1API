# Authentication System Documentation

## Overview

F1API now includes a complete authentication system with secure user registration, login, and session management.

## Features

- ✅ **User Registration** - Create new accounts with username, email, and password
- ✅ **Secure Login** - Password hashing with bcrypt
- ✅ **Session Management** - Secure cookie-based sessions
- ✅ **Protected Routes** - Use `@login_required` decorator
- ✅ **Flash Messages** - User feedback for actions
- ✅ **SQLite Database** - Persistent user storage

## Database Schema

The `users` table in `./data/users.db`:

````markdown
# Documentazione del sistema di autenticazione

## Panoramica

F1API include ora un sistema di autenticazione completo con registrazione sicura degli utenti, accesso (login) e gestione delle sessioni.

## Funzionalità

- ✅ **Registrazione utenti** - Creazione di nuovi account con username, email e password
- ✅ **Login sicuro** - Password memorizzate in forma hash con bcrypt
- ✅ **Gestione sessioni** - Sessioni sicure tramite cookie
- ✅ **Rotte protette** - Usa il decoratore `@login_required`
- ✅ **Messaggi flash** - Feedback visivo per le azioni dell'utente
- ✅ **Database SQLite** - Persistenza degli utenti

## Schema del database

La tabella `users` in `./data/users.db`:

```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TEXT NOT NULL,
    last_login TEXT
);
```

## Rotte

### Rotte pubbliche

- `GET /` - Pagina principale (mostra contenuti diversi per utenti autenticati)
- `GET /auth/register` - Form di registrazione
- `POST /auth/register` - Elabora la registrazione
- `GET /auth/login` - Form di login
- `POST /auth/login` - Elabora il login

### Rotte protette (richiedono login)

- `GET /auth/logout` - Logout (cancella la sessione)
- `GET /auth/profile` - Pagina profilo utente

## Esempi d'uso

### Registrare un nuovo utente

1. Vai su `/auth/register`
2. Compila:
   - Username (3-20 caratteri, alfanumerico + underscore)
   - Email (formato valido)
   - Password (minimo 6 caratteri)
   - Conferma password
3. Invia il form
4. Se la registrazione ha successo sarai reindirizzato alla pagina di login

### Login

1. Vai su `/auth/login`
2. Inserisci username e password
3. Invia il form
4. Se il login ha successo sarai reindirizzato alla home

### Proteggere una rotta

```python
from f1api.auth_decorators import login_required

@app.route('/protected')
@login_required
def protected_route():
    return "This requires login"
```

### Ottenere l'utente corrente

```python
from f1api.auth_decorators import get_current_user, is_authenticated

@app.route('/dashboard')
def dashboard():
    if is_authenticated():
        user = get_current_user()
        return f"Welcome {user['username']}"
    return "Please log in"
```

## Configurazione

Imposta queste variabili d'ambiente in `.env`:

```bash
# Chiave segreta di Flask per la gestione delle sessioni
SECRET_KEY=your-secret-key-here

# Percorso al database utenti
AUTH_DB_PATH=./data/users.db

# Sicurezza del cookie di sessione (metti True in produzione con HTTPS)
SESSION_COOKIE_SECURE=False
```

Generare una `SECRET_KEY` sicura:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

## Misure di sicurezza

1. **Hashing delle password** - Usa bcrypt con salting automatico
2. **Sessioni sicure** - Cookie con `HTTPOnly` per mitigare XSS
3. **Protezione CSRF** - Token di sessione per prevenire CSRF
4. **Validazione input** - Controlli su username, email e password
5. **Vincoli di unicità** - Previene duplicati di username/email

## Test

Esegui la suite di test per l'autenticazione:

```bash
python test_auth.py
```

Questo esegue:

- Creazione di un utente di test
- Verifica dell'hashing delle password
- Test di autenticazione
- Verifica delle funzioni del repository di autenticazione

## Integrazione con le rotte esistenti

Il sistema di autenticazione è già integrato con l'app:

- **Navigazione** - Pulsanti Login/Register oppure Profile/Logout nell'header
- **Home** - Mostra contenuti personalizzati per utenti autenticati
- **Messaggi flash** - Feedback per tutte le azioni di autenticazione
- **Stato di sessione** - Persiste tra le richieste

## Categorie dei messaggi flash

- `success` - Verde, per operazioni riuscite
- `danger` - Rosso, per errori
- `warning` - Giallo, per avvisi
- `info` - Blu, per messaggi informativi

## API

### AuthRepository

```python
from f1api.auth_repository import get_auth_repo

auth = get_auth_repo()

# Create user
user_id = auth.create_user("username", "email@example.com", "password")

# Authenticate
user = auth.authenticate("username", "password")

# Get user
user = auth.get_user_by_username("username")
user = auth.get_user_by_id(user_id)

# Check existence
exists = auth.username_exists("username")
exists = auth.email_exists("email@example.com")

# Update last login (automatic on authenticate)
auth.update_last_login(user_id)
```

## Risoluzione dei problemi

**Problema**: "Import bcrypt could not be resolved"  
**Soluzione**: Installa bcrypt: `pip install bcrypt`

**Problema**: La sessione non persiste  
**Soluzione**: Assicurati che `SECRET_KEY` sia impostata nell'ambiente o in `.env`

**Problema**: Errori sul database  
**Soluzione**: Verifica che la cartella `./data/` esista ed sia scrivibile

**Problema**: I messaggi flash non vengono mostrati  
**Soluzione**: Assicurati che il tuo template estenda `base.html`

## Miglioramenti futuri

Possibili estensioni:

- Reset password via email
- Autenticazione a due fattori (2FA)
- Integrazione OAuth (Google, GitHub, ecc.)
- Limitazione delle richieste per tentativi di login
- Requisiti di robustezza delle password
- Ruoli utente e permessi
- Verifica email
- Funzionalità "remember me"
- Eliminazione account
- Modifica profilo

## Struttura dei file

```text
src/f1api/
├── auth_repository.py       # User database operations
├── auth_decorators.py       # Login required decorator
├── routes/
│   ├── auth.py             # Auth routes (login, register, etc.)
│   └── main.py             # Home page route
├── templates/
│   ├── base.html           # Base template with auth nav
│   ├── home.html           # Home page
│   ├── login.html          # Login form
│   ├── register.html       # Registration form
│   └── profile.html        # User profile
└── static/css/
    └── style.css           # Styles for auth UI

data/
└── users.db                # SQLite user database
```
