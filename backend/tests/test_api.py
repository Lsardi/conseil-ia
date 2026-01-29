"""Tests des endpoints API."""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient) -> None:
    """Le health check retourne un status healthy."""
    response = await client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data
    assert "models_configured" in data


@pytest.mark.asyncio
async def test_list_models(client: AsyncClient) -> None:
    """L'endpoint /models retourne la liste des modèles."""
    response = await client.get("/api/v1/models")
    assert response.status_code == 200
    data = response.json()
    assert "models" in data
    model_names = [m["name"] for m in data["models"]]
    assert "claude" in model_names
    assert "gpt4" in model_names
    assert "gemini" in model_names
    assert "ollama" in model_names


@pytest.mark.asyncio
async def test_stats_endpoint(client: AsyncClient) -> None:
    """L'endpoint /stats retourne les statistiques."""
    response = await client.get("/api/v1/stats")
    assert response.status_code == 200
    data = response.json()
    assert "total_requests" in data
    assert "total_cost" in data


@pytest.mark.asyncio
async def test_ask_validation_error(client: AsyncClient) -> None:
    """Une question vide retourne une erreur 422."""
    response = await client.post(
        "/api/v1/council/ask",
        json={"question": ""},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_ask_invalid_model(client: AsyncClient) -> None:
    """Un modèle invalide retourne une erreur 422."""
    response = await client.post(
        "/api/v1/council/ask",
        json={"question": "test", "models": ["invalid_model"]},
    )
    assert response.status_code == 422
