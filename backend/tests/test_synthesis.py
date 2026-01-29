"""Tests du service de synthèse."""

from __future__ import annotations

import pytest

from app.models.base import ModelResult
from app.services.synthesis import SynthesisService


@pytest.fixture
def synthesis():
    return SynthesisService()


@pytest.fixture
def sample_results():
    return {
        "claude": ModelResult(
            content="La photosynthèse est le processus par lequel les plantes convertissent la lumière en énergie.",
            model_name="claude",
            tokens_input=50,
            tokens_output=100,
        ),
        "gpt4": ModelResult(
            content="Photosynthesis is the process where plants convert sunlight into chemical energy.",
            model_name="gpt4",
            tokens_input=50,
            tokens_output=80,
        ),
    }


def test_calculate_consensus_single_model(synthesis: SynthesisService) -> None:
    """Un seul modèle donne un consensus de 1.0."""
    results = {
        "claude": ModelResult(content="test", model_name="claude"),
    }
    score = synthesis.calculate_consensus(results)
    assert score == 1.0


def test_calculate_consensus_similar(synthesis: SynthesisService) -> None:
    """Des réponses similaires donnent un score élevé."""
    results = {
        "a": ModelResult(content="the cat sat on the mat today", model_name="a"),
        "b": ModelResult(content="the cat sat on the mat yesterday", model_name="b"),
    }
    score = synthesis.calculate_consensus(results)
    assert score > 0.5


def test_calculate_consensus_different(synthesis: SynthesisService) -> None:
    """Des réponses très différentes donnent un score bas."""
    results = {
        "a": ModelResult(
            content="quantum mechanics describes subatomic particles",
            model_name="a",
        ),
        "b": ModelResult(
            content="baking bread requires flour water yeast salt",
            model_name="b",
        ),
    }
    score = synthesis.calculate_consensus(results)
    assert score < 0.3


@pytest.mark.asyncio
async def test_synthesize_no_results(synthesis: SynthesisService) -> None:
    """Aucun résultat valide produit un message d'erreur."""
    result = await synthesis.synthesize("test", {})
    assert "aucun" in result.lower()


@pytest.mark.asyncio
async def test_synthesize_single_result(synthesis: SynthesisService) -> None:
    """Un seul résultat est retourné directement."""
    results = {
        "claude": ModelResult(content="Ma réponse", model_name="claude"),
    }
    result = await synthesis.synthesize("test", results)
    assert "Ma réponse" in result


@pytest.mark.asyncio
async def test_synthesize_multiple_results(
    synthesis: SynthesisService, sample_results: dict
) -> None:
    """Plusieurs résultats produisent une synthèse structurée."""
    result = await synthesis.synthesize("Qu'est-ce que la photosynthèse ?", sample_results)
    assert "Synthèse" in result
    assert "claude" in result
    assert "gpt4" in result


@pytest.mark.asyncio
async def test_debate_format(
    synthesis: SynthesisService, sample_results: dict
) -> None:
    """Le mode débat produit un format correct."""
    result = await synthesis.create_debate("test", sample_results)
    assert "Débat" in result
    assert "claude" in result
    assert "gpt4" in result
