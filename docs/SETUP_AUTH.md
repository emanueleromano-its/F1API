# 🏎️ F1API - Sistema Completo con Autenticazione

## ✅ Implementazione Completata

Ho implementato un sistema di autenticazione completo per la tua applicazione F1API con le seguenti funzionalità:

### 🔐 Funzionalità Implementate

1. **Home Page (`/`)**
   - Landing page accattivante con design F1
   - Contenuto diverso per utenti loggati/non loggati
   - Link rapidi a tutte le sezioni principali

2. **Sistema di Autenticazione**
   - Registrazione utenti con validazione (`/auth/register`)
   - Login sicuro con bcrypt (`/auth/login`)
   - Logout (`/auth/logout`)
   - Pagina profilo protetta (`/auth/profile`)

3. **Sicurezza**
   - Password hashing con bcrypt
   - Sessioni sicure con cookie HTTPOnly
   - Validazione input (username, email, password)
   - Constraint di unicità per username/email
   - SECRET_KEY configurabile

4. **Database SQLite**
   - Tabella `users` con tutti i campi necessari
   - Indici per performance
   - Thread-safe operations

5. **UI/UX**
   - Flash messages per feedback utente
   - Template responsive che estendono base.html
   - Design coerente con tema F1
   - Navigation bar dinamica (Login/Register o Profile/Logout)

## 📁 File Creati/Modificati

### Nuovi File

```text
src/f1api/
├── auth_repository.py          # Repository per gestione utenti
├── auth_decorators.py          # Decoratori @login_required
├── routes/auth.py              # Route autenticazione
├── templates/
│   ├── home.html              # Home page
│   ├── login.html             # Form login
│   ├── register.html          # Form registrazione
│   └── profile.html           # Profilo utente
│
test_auth.py                   # Script di test autenticazione
generate_secret_key.py         # Genera SECRET_KEY sicura
README_AUTH.md                 # Documentazione completa
```

### File Modificati

```text
src/f1api/
├── app.py                     # Aggiunto auth_bp, SECRET_KEY config
├── routes/main.py             # Cambiato / da JSON a HTML home
├── templates/base.html        # Aggiunto nav dinamico + flash messages
└── static/css/style.css       # Stili per flash messages

requirements.txt               # Aggiunto bcrypt
.env.example                   # Aggiunte variabili AUTH_DB_PATH, SECRET_KEY
```

## 🚀 Setup Rapido

### 1. Installa Dipendenze

```bash
pip install bcrypt
```

O installa tutte le dipendenze:

```bash
pip install -r requirements.txt
```

### 2. Genera SECRET_KEY

```bash
python generate_secret_key.py
```

Copia l'output nel tuo file `.env`:

```bash
SECRET_KEY=<generated_key_qui>
```

### 3. Configura .env

Crea/aggiorna il file `.env` con:

```bash
# Flask
PORT=5000
SECRET_KEY=your-generated-secret-key-here

# Database
AUTH_DB_PATH=./data/users.db
CACHE_DB_PATH=./data/cache.db

# API
F1OPEN_API_BASE=https://api.openf1.org/v1
CACHE_TTL_SECONDS=300
```

### 4. Testa il Sistema

```bash
python test_auth.py
```

Questo creerà un utente di test e verificherà tutte le funzionalità.

### 5. Avvia l'Applicazione

```bash
python -m f1api.app
```

Oppure:

```bash
flask --app src.f1api.app run
```

### 6. Accedi all'App

Apri il browser su: `http://localhost:5000`

## 🎯 Come Usare

### Registrazione

1. Vai su `/auth/register`
2. Compila il form:
   - Username: 3-20 caratteri (lettere, numeri, underscore)
   - Email: formato valido
   - Password: minimo 6 caratteri
3. Clicca "Create Account"
4. Verrai reindirizzato al login

### Login

1. Vai su `/auth/login`
2. Inserisci username e password
3. Clicca "Login"
4. Verrai reindirizzato alla home page

### Navigazione

- **Home** (`/`) - Dashboard principale
- **Drivers** (`/drivers`) - Lista piloti
- **Teams** (`/teams`) - Scuderie e macchine
- **Races** (`/races`) - Calendario gare
- **Profile** (`/auth/profile`) - Profilo utente (richiede login)

### Proteggere una Route

Per richiedere l'autenticazione su una tua route:

```python
from f1api.auth_decorators import login_required

@app.route('/mia-route-protetta')
@login_required
def mia_route():
    return "Solo utenti loggati possono vedere questo"
```

### Ottenere Utente Corrente

```python
from f1api.auth_decorators import get_current_user, is_authenticated

@app.route('/dashboard')
def dashboard():
    if is_authenticated():
        user = get_current_user()
        return f"Benvenuto {user['username']}"
    return redirect('/auth/login')
```

## 🔍 Dettagli Tecnici

### Schema Database `users`

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

### Validazione

- **Username**: 3-20 caratteri, solo alfanumerici + underscore
- **Email**: formato email valido (regex)
- **Password**: minimo 6 caratteri
- Verifica unicità username/email

### Sessioni

- Cookie HTTPOnly per prevenire XSS
- SameSite=Lax per protezione CSRF
- Timeout: 1 ora (configurabile)
- SECRET_KEY per firma sicura

### Hash Password

- Algoritmo: bcrypt
- Salt automatico per ogni password
- Computation cost adeguato

## 📊 Struttura Route

```text
/ (GET)                        → Home page
/api (GET)                     → API info (JSON)

/auth/register (GET/POST)      → Registrazione
/auth/login (GET/POST)         → Login
/auth/logout (GET)             → Logout (richiede login)
/auth/profile (GET)            → Profilo (richiede login)

/drivers (GET)                 → Lista piloti
/driver/<id> (GET)             → Dettaglio pilota
/teams (GET)                   → Lista team
/races (GET)                   → Lista gare

/cache/stats (GET)             → Statistiche cache
/cache/clear (POST)            → Pulisci cache
/cache/cleanup (POST)          → Rimuovi cache scaduta
```

## 🎨 UI Features

### Flash Messages

I messaggi vengono mostrati automaticamente in 4 colori:

- 🟢 **Success** - Operazioni riuscite
- 🔴 **Danger** - Errori
- 🟡 **Warning** - Avvisi
- 🔵 **Info** - Informazioni

### Navigation Dinamica

L'header mostra automaticamente:

- **Non loggato**: Login | Register
- **Loggato**: Profile | Logout

### Design Responsive

Tutti i template sono mobile-friendly e seguono il tema F1.

## 🔧 Troubleshooting

### Errore: "Import bcrypt could not be resolved"

```bash
pip install bcrypt
```

### Errore: "No SECRET_KEY set"

Genera una chiave e aggiungila al `.env`:

```bash
python generate_secret_key.py
```

### Errore database

Assicurati che `./data/` esista e sia scrivibile:

```bash
mkdir -p data
```

### Sessione non persiste

Verifica che `SECRET_KEY` sia impostata nel `.env` o nelle variabili d'ambiente.

## 📚 Documentazione

- **README_AUTH.md** - Documentazione completa del sistema auth
- **test_auth.py** - Script di test con esempi d'uso
- **.env.example** - Tutte le variabili configurabili

## 🎉 Prossimi Passi

L'applicazione è pronta! Puoi:

1. **Personalizzare** - Modifica template e stili
2. **Estendere** - Aggiungi ruoli utente, permessi, etc.
3. **Proteggere** - Usa `@login_required` sulle tue route
4. **Distribuire** - Deploy su Heroku, Railway, o altro PaaS

## 🛡️ Sicurezza in Produzione

Per il deploy in produzione, assicurati di:

1. ✅ Impostare `SECRET_KEY` univoca e sicura
2. ✅ Impostare `SESSION_COOKIE_SECURE=True` (richiede HTTPS)
3. ✅ Usare database production-ready (PostgreSQL)
4. ✅ Abilitare rate limiting
5. ✅ Implementare logging appropriato
6. ✅ Validare tutti gli input
7. ✅ Aggiungere HTTPS/TLS

## 📞 Supporto

Per domande o problemi:

- Controlla `README_AUTH.md`
- Esegui `test_auth.py` per verificare il setup
- Controlla i log Flask per errori dettagliati

---

**Fatto! 🎊** Il tuo sistema di autenticazione è completo e pronto all'uso!
