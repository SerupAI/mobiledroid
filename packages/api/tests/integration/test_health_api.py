"""Integration tests for Health and Root API endpoints."""

import pytest


@pytest.mark.asyncio
class TestHealthAPI:
    """Tests for /health endpoint."""

    async def test_health_check(self, client):
        """Test health check endpoint returns healthy status."""
        response = await client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data

    async def test_health_check_returns_version(self, client):
        """Test health check returns application version."""
        response = await client.get("/health")

        data = response.json()
        assert data["version"] is not None
        # Version should be in semver format
        version = data["version"]
        assert "." in version


@pytest.mark.asyncio
class TestRootAPI:
    """Tests for / endpoint."""

    async def test_root_endpoint(self, client):
        """Test root endpoint returns API info."""
        response = await client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "version" in data
        assert "docs" in data
        assert "health" in data

    async def test_root_docs_url(self, client):
        """Test root endpoint returns correct docs URL."""
        response = await client.get("/")

        data = response.json()
        assert data["docs"] == "/docs"
        assert data["health"] == "/health"


@pytest.mark.asyncio
class TestOpenAPISchema:
    """Tests for OpenAPI schema."""

    async def test_openapi_json_available(self, client):
        """Test OpenAPI JSON is accessible."""
        response = await client.get("/openapi.json")

        assert response.status_code == 200
        data = response.json()
        assert "openapi" in data
        assert "paths" in data
        assert "info" in data

    async def test_openapi_contains_profiles_endpoints(self, client):
        """Test OpenAPI schema contains profiles endpoints."""
        response = await client.get("/openapi.json")

        data = response.json()
        paths = data["paths"]

        assert "/profiles" in paths
        assert "/profiles/{profile_id}" in paths
        assert "/profiles/{profile_id}/start" in paths
        assert "/profiles/{profile_id}/stop" in paths
