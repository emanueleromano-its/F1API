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

## Routes

### Public Routes

- `GET /` - Home page (shows different content for logged-in users)
- `GET /auth/register` - Registration form
- `POST /auth/register` - Process registration
- `GET /auth/login` - Login form
- `POST /auth/login` - Process login

### Protected Routes (require login)

- `GET /auth/logout` - Logout (clears session)
- `GET /auth/profile` - User profile page

## Usage Examples

### Register a New User

1. Navigate to `/auth/register`
2. Fill in:
   - Username (3-20 chars, alphanumeric + underscore)
   - Email (valid email format)
   - Password (minimum 6 characters)
   - Confirm password
3. Submit the form
4. On success, you'll be redirected to login

### Login

1. Navigate to `/auth/login`
2. Enter username and password
3. Submit the form
4. On success, you'll be redirected to the home page

### Protect a Route

```python
from f1api.auth_decorators import login_required

@app.route('/protected')
@login_required
def protected_route():
    return "This requires login"
```

### Get Current User

```python
from f1api.auth_decorators import get_current_user, is_authenticated

@app.route('/dashboard')
def dashboard():
    if is_authenticated():
        user = get_current_user()
        return f"Welcome {user['username']}"
    return "Please log in"
```

## Configuration

Set these environment variables in `.env`:

```bash
# Flask secret key for session management
SECRET_KEY=your-secret-key-here

# Path to users database
AUTH_DB_PATH=./data/users.db

# Session cookie security (set to True in production with HTTPS)
SESSION_COOKIE_SECURE=False
```

Generate a secure SECRET_KEY:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

## Security Features

1. **Password Hashing** - Uses bcrypt with automatic salting
2. **Secure Sessions** - HTTPOnly cookies prevent XSS
3. **CSRF Protection** - Session tokens protect against CSRF
4. **Input Validation** - Username, email, and password validation
5. **Unique Constraints** - Prevents duplicate usernames/emails

## Testing

Run the authentication test suite:

```bash
python test_auth.py
```

This will:

- Create a test user
- Test password hashing
- Test authentication
- Verify all auth repository functions

## Integration with Existing Routes

The authentication system is already integrated:

- **Navigation** - Login/Register or Profile/Logout buttons in header
- **Home Page** - Shows personalized content for logged-in users
- **Flash Messages** - Feedback for all auth actions
- **Session State** - Persists across requests

## Flash Message Categories

- `success` - Green, for successful operations
- `danger` - Red, for errors
- `warning` - Yellow, for warnings
- `info` - Blue, for informational messages

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

## Troubleshooting

**Problem**: "Import bcrypt could not be resolved"  
**Solution**: Install bcrypt: `pip install bcrypt`

**Problem**: Session not persisting  
**Solution**: Make sure `SECRET_KEY` is set in environment or `.env`

**Problem**: Database errors  
**Solution**: Check `./data/` directory exists and is writable

**Problem**: Flash messages not showing  
**Solution**: Make sure your template extends `base.html`

## Future Enhancements

Possible improvements:

- Password reset via email
- Two-factor authentication
- OAuth integration (Google, GitHub, etc.)
- Rate limiting for login attempts
- Password strength requirements
- User roles and permissions
- Email verification
- Remember me functionality
- Account deletion
- Profile editing

## File Structure

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

## License

Same as F1API project.
