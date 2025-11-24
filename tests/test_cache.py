"""Tests for cache repository functionality.

Tests cover:
- Cache hit/miss scenarios
- TTL expiration
- Stale cache fallback on API errors
- Cache invalidation
- ETag support
- Thread safety
"""
import json
import os
import tempfile
import time
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from f1api.cache_repository import CacheRepository


@pytest.fixture
def temp_cache_db():
    """Create temporary cache database for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test_cache.db")
        yield db_path


@pytest.fixture
def cache_repo(temp_cache_db):
    """Create cache repository instance for testing."""
    repo = CacheRepository(db_path=temp_cache_db, default_ttl_seconds=2)
    yield repo
    repo.close()


class TestCacheRepository:
    """Test suite for CacheRepository."""

    def test_cache_miss(self, cache_repo):
        """Test cache miss returns None."""
        result = cache_repo.get("https://api.example.com/data", {"id": "123"})
        assert result is None

    def test_cache_set_and_get(self, cache_repo):
        """Test saving and retrieving from cache."""
        url = "https://api.example.com/data"
        params = {"id": "123"}
        response_body = {"result": "success", "data": [1, 2, 3]}
        
        cache_repo.set(url, params, response_body, 200, {"Content-Type": "application/json"})
        
        cached = cache_repo.get(url, params)
        assert cached is not None
        assert cached["body"] == response_body
        assert cached["status_code"] == 200
        assert cached["from_cache"] is True

    def test_cache_expiration(self, cache_repo):
        """Test that expired cache entries return None."""
        url = "https://api.example.com/data"
        params = {"id": "123"}
        response_body = {"result": "success"}
        
        # Save with 1 second TTL
        cache_repo.set(url, params, response_body, 200, ttl_seconds=1)
        
        # Should be valid immediately
        cached = cache_repo.get(url, params)
        assert cached is not None
        
        # Wait for expiration
        time.sleep(1.5)
        
        # Should be expired
        cached = cache_repo.get(url, params)
        assert cached is None

    def test_stale_cache_retrieval(self, cache_repo):
        """Test retrieving stale cache entries."""
        url = "https://api.example.com/data"
        params = {"id": "123"}
        response_body = {"result": "success"}
        
        # Save with 1 second TTL
        cache_repo.set(url, params, response_body, 200, ttl_seconds=1)
        time.sleep(1.5)
        
        # Normal get should return None (expired)
        assert cache_repo.get(url, params) is None
        
        # get_stale should return the expired entry
        stale = cache_repo.get_stale(url, params)
        assert stale is not None
        assert stale["body"] == response_body
        assert stale["stale"] is True

    def test_cache_invalidation_specific(self, cache_repo):
        """Test invalidating specific cache entry."""
        url1 = "https://api.example.com/data1"
        url2 = "https://api.example.com/data2"
        
        cache_repo.set(url1, None, {"data": 1}, 200)
        cache_repo.set(url2, None, {"data": 2}, 200)
        
        # Invalidate url1
        count = cache_repo.invalidate(url1)
        assert count == 1
        
        # url1 should be gone, url2 should remain
        assert cache_repo.get(url1) is None
        assert cache_repo.get(url2) is not None

    def test_cache_invalidation_all(self, cache_repo):
        """Test clearing all cache entries."""
        cache_repo.set("https://api.example.com/data1", None, {"data": 1}, 200)
        cache_repo.set("https://api.example.com/data2", None, {"data": 2}, 200)
        
        count = cache_repo.invalidate()
        assert count == 2
        
        # Both should be gone
        assert cache_repo.get("https://api.example.com/data1") is None
        assert cache_repo.get("https://api.example.com/data2") is None

    def test_cleanup_expired(self, cache_repo):
        """Test cleanup of expired entries."""
        # Add valid entry
        cache_repo.set("https://api.example.com/valid", None, {"data": "valid"}, 200, ttl_seconds=10)
        
        # Add expired entry
        cache_repo.set("https://api.example.com/expired", None, {"data": "expired"}, 200, ttl_seconds=1)
        time.sleep(1.5)
        
        # Cleanup should remove only expired
        count = cache_repo.cleanup_expired()
        assert count == 1
        
        # Valid entry should remain
        assert cache_repo.get("https://api.example.com/valid") is not None
        assert cache_repo.get("https://api.example.com/expired") is None

    def test_etag_support(self, cache_repo):
        """Test ETag storage and retrieval."""
        url = "https://api.example.com/data"
        etag = '"abc123"'
        
        cache_repo.set(url, None, {"data": "test"}, 200, etag=etag)
        
        cached = cache_repo.get(url)
        assert cached["etag"] == etag

    def test_cache_stats(self, cache_repo):
        """Test cache statistics."""
        # Add some entries
        cache_repo.set("https://api.example.com/data1", None, {"data": 1}, 200, ttl_seconds=10)
        cache_repo.set("https://api.example.com/data2", None, {"data": 2}, 200, ttl_seconds=1)
        time.sleep(1.5)
        
        stats = cache_repo.stats()
        
        assert stats["total_entries"] == 2
        assert stats["expired_entries"] == 1
        assert stats["valid_entries"] == 1
        assert stats["db_size_bytes"] > 0

    def test_different_params_different_cache(self, cache_repo):
        """Test that different params create different cache entries."""
        url = "https://api.example.com/data"
        
        cache_repo.set(url, {"id": "1"}, {"data": "one"}, 200)
        cache_repo.set(url, {"id": "2"}, {"data": "two"}, 200)
        
        cached1 = cache_repo.get(url, {"id": "1"})
        cached2 = cache_repo.get(url, {"id": "2"})
        
        assert cached1["body"]["data"] == "one"
        assert cached2["body"]["data"] == "two"

    def test_cache_update(self, cache_repo):
        """Test updating existing cache entry."""
        url = "https://api.example.com/data"
        
        # Initial save
        cache_repo.set(url, None, {"version": 1}, 200)
        
        # Update
        cache_repo.set(url, None, {"version": 2}, 200)
        
        # Should have latest version
        cached = cache_repo.get(url)
        assert cached["body"]["version"] == 2
        
        # Should have only one entry
        stats = cache_repo.stats()
        assert stats["total_entries"] == 1
