from __future__ import annotations

from typing import Any, Dict, Optional

from flask import Blueprint, jsonify, request

from f1api.api import fetch_from_f1open, get_cache_repo

main_bp = Blueprint("main", __name__)


@main_bp.route("/", methods=["GET"])
def index():
    return jsonify({
        "service": "F1API with persistent SQLite cache",
        "endpoints": [
            {"path": "/drivers", "desc": "Elenca o cerca piloti"},
            {"path": "/drivers/<id>", "desc": "Dettagli pilota"},
            {"path": "/teams", "desc": "Elenca i team"},
            {"path": "/races", "desc": "Elenca le gare"},
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
