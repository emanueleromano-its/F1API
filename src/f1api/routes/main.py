from __future__ import annotations

from typing import Any, Dict, Optional

from flask import Blueprint, jsonify, request, render_template, session, flash, redirect, url_for

from f1api.api import fetch_from_f1open, get_cache_repo
from f1api.auth_decorators import is_authenticated, get_current_user, login_required
from f1api.auth_repository import get_auth_repo

main_bp = Blueprint("main", __name__)


@main_bp.route("/", methods=["GET"])
def home():
    """Home page - landing page with auth status."""
    user = get_current_user() if is_authenticated() else None
    return render_template("home.html", user=user)


@main_bp.route("/api", methods=["GET"])
def api_info():
    """API information endpoint (JSON)."""
    return jsonify({
        "service": "F1API with persistent SQLite cache",
        "endpoints": [
            {"path": "/", "desc": "Home page"},
            {"path": "/drivers", "desc": "Elenca o cerca piloti"},
            {"path": "/driver/<id>", "desc": "Dettagli pilota"},
            {"path": "/teams", "desc": "Elenca i team"},
            {"path": "/races", "desc": "Elenca le gare"},
            {"path": "/auth/register", "desc": "User registration"},
            {"path": "/auth/login", "desc": "User login"},
            {"path": "/auth/logout", "desc": "User logout"},
            {"path": "/auth/profile", "desc": "User profile (protected)"},
            {"path": "/cache/stats", "desc": "Cache statistics"},
            {"path": "/cache/clear", "desc": "Clear all cache (POST)"},
            {"path": "/cache/cleanup", "desc": "Remove expired entries (POST)"},
        ],
    })


@main_bp.route("/position", methods=["GET"])
def position():
    data = fetch_from_f1open("position")
    return jsonify(data)


@main_bp.route("/cache/stats", methods=["GET"])
def cache_stats():
    """Get cache statistics."""
    cache = get_cache_repo()
    stats = cache.stats()
    return jsonify(stats)


@main_bp.route("/cache/clear", methods=["POST"])
def cache_clear():
    """Clear all cache entries or specific URL."""
    cache = get_cache_repo()
    url = request.args.get("url")
    
    if url:
        count = cache.invalidate(url=url)
        return jsonify({"message": f"Invalidated {count} cache entry/entries for URL", "url": url})
    else:
        count = cache.invalidate()
        return jsonify({"message": f"Cleared all cache ({count} entries)"})


@main_bp.route("/cache/cleanup", methods=["POST"])
def cache_cleanup():
    """Remove expired cache entries."""
    cache = get_cache_repo()
    count = cache.cleanup_expired()
    return jsonify({"message": f"Removed {count} expired entries"})


@main_bp.route("/history", methods=["GET"])
@login_required
def history():
    """Display user's navigation history."""
    user = get_current_user()
    auth_repo = get_auth_repo()
    
    # Get history records
    history_records = auth_repo.get_user_history(session["user_id"], limit=100)
    
    return render_template("history.html", user=user, history=history_records)


@main_bp.route("/history/clear", methods=["POST"])
@login_required
def clear_history():
    """Clear user's navigation history."""
    auth_repo = get_auth_repo()
    count = auth_repo.clear_user_history(session["user_id"])
    flash(f"Successfully cleared {count} history records.", "success")
    return redirect(url_for("main.history"))
