"""Authentication routes for F1API."""
from __future__ import annotations

import re
from typing import Any

from flask import Blueprint, render_template, request, redirect, url_for, session, flash

from f1api.auth_repository import get_auth_repo
from f1api.auth_decorators import login_required

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


def is_valid_email(email: str) -> bool:
    """Valida il formato di un indirizzo email.

    Argomenti:
        email: indirizzo email da validare

    Ritorna:
        True se il formato è valido, False altrimenti
    """
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def is_valid_username(username: str) -> bool:
    """Valida il formato dello username.

    Argomenti:
        username: username da validare

    Ritorna:
        True se valido (3-20 caratteri, alfanumerico e underscore), False altrimenti
    """
    pattern = r'^[a-zA-Z0-9_]{3,20}$'
    return re.match(pattern, username) is not None


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    """Pagina di registrazione utente."""
    if request.method == "GET":
        return render_template("register.html")
    
    # POST: elabora la registrazione
    username = request.form.get("username", "").strip()
    email = request.form.get("email", "").strip()
    password = request.form.get("password", "")
    password_confirm = request.form.get("password_confirm", "")
    
    # Validazione
    errors = []
    
    if not username:
        errors.append("Username is required.")
    elif not is_valid_username(username):
        errors.append("Username must be 3-20 characters (letters, numbers, underscore only).")
    
    if not email:
        errors.append("Email is required.")
    elif not is_valid_email(email):
        errors.append("Invalid email format.")
    
    if not password:
        errors.append("Password is required.")
    elif len(password) < 6:
        errors.append("Password must be at least 6 characters.")
    
    if password != password_confirm:
        errors.append("Passwords do not match.")
    
    if errors:
        for error in errors:
            flash(error, "danger")
        return render_template("register.html", username=username, email=email)
    
    # Verifica se username o email esistono già
    auth_repo = get_auth_repo()
    
    if auth_repo.username_exists(username):
        flash("Username already exists. Please choose another.", "danger")
        return render_template("register.html", username="", email=email)
    
    if auth_repo.email_exists(email):
        flash("Email already registered. Please use another or log in.", "danger")
        return render_template("register.html", username=username, email="")
    
    # Crea utente
    user_id = auth_repo.create_user(username, email, password)
    
    if user_id:
        flash("Registration successful! Please log in.", "success")
        return redirect(url_for("auth.login"))
    else:
        flash("Registration failed. Please try again.", "danger")
        return render_template("register.html", username=username, email=email)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    """Pagina di login utente."""
    if request.method == "GET":
        return render_template("login.html")
    
    # POST: elabora il login
    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")
    
    if not username or not password:
        flash("Username and password are required.", "danger")
        return render_template("login.html", username=username)
    
    # Autentica
    auth_repo = get_auth_repo()
    user = auth_repo.authenticate(username, password)
    
    if user:
    # Imposta la sessione
        session["user_id"] = user["id"]
        session["username"] = user["username"]
        flash(f"Welcome back, {user['username']}!", "success")
        
    # Reindirizza alla pagina successiva o alla home
        next_page = request.args.get("next")
        if next_page:
            return redirect(next_page)
        return redirect(url_for("main.home"))
    else:
        flash("Invalid username or password.", "danger")
        return render_template("login.html", username=username)


@auth_bp.route("/logout")
@login_required
def logout():
    """Logout utente."""
    username = session.get("username", "User")
    session.clear()
    flash(f"Goodbye, {username}! You have been logged out.", "info")
    return redirect(url_for("main.home"))


@auth_bp.route("/profile")
@login_required
def profile():
    """Pagina profilo utente (protetta)."""
    from f1api.auth_decorators import get_current_user
    user = get_current_user()
    return render_template("profile.html", user=user)
