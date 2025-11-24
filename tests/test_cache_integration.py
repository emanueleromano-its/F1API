"""Integration tests for cache-enabled API endpoints.

Tests the full request/response cycle with caching.
"""
import json
import os
import tempfile
import time
from unittest.mock import patch, MagicMock

import pytest

from f1api.app import create_app
from f1api.cache_repository import CacheRepository


@pytest.fixture
def temp_cache_db():
    """Create temporary cache database for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test_cache.db")
        os.environ["CACHE_DB_PATH"] = db_path
        os.environ["CACHE_TTL_SECONDS"] = "2"
        yield db_path
        # Cleanup
        if "CACHE_DB_PATH" in os.environ:
            del os.environ["CACHE_DB_PATH"]
        if "CACHE_TTL_SECONDS" in os.environ:
            del os.environ["CACHE_TTL_SECONDS"]


@pytest.fixture
def app(temp_cache_db):
    """Create Flask app for testing."""
    app = create_app({"TESTING": True})
    return app


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


class TestCacheIntegration:
    """Integration tests for cached API endpoints."""

    @patch("f1api.api.requests.get")
    def test_cache_miss_calls_api(self, mock_get, client):
        """Test that cache miss results in API call."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [{"driver": "Verstappen"}]
        mock_response.headers = {}
        mock_get.return_value = mock_response
        
        # First request should call API
        response = client.get("/drivers")
        assert response.status_code == 200
        assert mock_get.call_count == 1

    @patch("f1api.api.requests.get")
    def test_cache_hit_skips_api(self, mock_get, client):
        """Test that cache hit skips API call."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [{"driver": "Verstappen"}]
        mock_response.headers = {}
        mock_get.return_value = mock_response
        
        # First request populates cache
        client.get("/drivers")
        assert mock_get.call_count == 1
        
        # Second request should use cache
        client.get("/drivers")
        assert mock_get.call_count == 1  # Still 1, no new call

    @patch("f1api.api.requests.get")
    def test_cache_expiration_triggers_refresh(self, mock_get, client):
        """Test that expired cache triggers new API call."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [{"driver": "Verstappen"}]
        mock_response.headers = {}
        mock_get.return_value = mock_response
        
        # First request
        client.get("/drivers")
        assert mock_get.call_count == 1
        
        # Wait for expiration (TTL is 2 seconds in fixture)
        time.sleep(2.5)
        
        # Second request should call API again
        client.get("/drivers")
        assert mock_get.call_count == 2

    def test_cache_stats_endpoint(self, client):
        """Test cache stats endpoint."""
        response = client.get("/cache/stats")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert "total_entries" in data
        assert "db_path" in data

    @patch("f1api.api.requests.get")
    def test_cache_clear_endpoint(self, mock_get, client):
        """Test cache clear endpoint."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [{"driver": "Verstappen"}]
        mock_response.headers = {}
        mock_get.return_value = mock_response
        
        # Populate cache
        client.get("/drivers")
        assert mock_get.call_count == 1
        
        # Clear cache
        response = client.post("/cache/clear")
        assert response.status_code == 200
        
        # Next request should call API again
        client.get("/drivers")
        assert mock_get.call_count == 2

    @patch("f1api.api.requests.get")
    def test_api_error_uses_stale_cache(self, mock_get, client):
        """Test fallback to stale cache on API error."""
        # First successful request
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [{"driver": "Verstappen"}]
        mock_response.headers = {}
        mock_get.return_value = mock_response
        
        response = client.get("/drivers")
        assert response.status_code == 200
        
        # Wait for cache to expire
        time.sleep(2.5)
        
        # Second request fails
        import requests
        mock_get.side_effect = requests.RequestException("API down")
        
        # Should still get response from stale cache
        response = client.get("/drivers")
        assert response.status_code == 200
        # Note: The actual response will depend on how the route handles the data

    @patch("f1api.api.requests.get")
    def test_etag_conditional_request(self, mock_get, client):
        """Test that ETag is used for conditional requests."""
        # First request with ETag
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [{"driver": "Verstappen"}]
        mock_response.headers = {"ETag": '"abc123"'}
        mock_get.return_value = mock_response
        
        client.get("/drivers")
        
        # Wait for expiration
        time.sleep(2.5)
        
        # Second request should send If-None-Match
        # Reset mock to return 304
        mock_response_304 = MagicMock()
        mock_response_304.status_code = 304
        mock_response_304.headers = {"ETag": '"abc123"'}
        mock_get.return_value = mock_response_304
        
        client.get("/drivers")
        
        # Verify If-None-Match header was sent
        call_args = mock_get.call_args
        assert "If-None-Match" in call_args.kwargs.get("headers", {})
