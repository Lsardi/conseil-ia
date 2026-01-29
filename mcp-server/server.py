"""Serveur MCP pour le Conseil des IA.

Expose le conseil comme outil utilisable depuis Claude Desktop
ou tout client MCP compatible.
"""

from __future__ import annotations

import json
import logging
import os
from typing import Any

import httpx
from mcp.server.fastmcp import FastMCP

# Configuration
API_URL = os.getenv("CONSEIL_API_URL", "http://localhost:8080")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("conseil_ia.mcp")

mcp = FastMCP(
    "Conseil des IA",
    description=(
        "Interroge simultanément plusieurs modèles IA "
        "(Claude, GPT-4, Gemini, Mistral, DeepSeek, Cohere, Ollama) "
        "et synthétise leurs réponses."
    ),
)


@mcp.tool()
async def ask_conseil(
    question: str,
    mode: str = "synthesis",
    models: str = "claude,gpt4,gemini",
) -> str:
    """Pose une question au conseil des IA.

    Args:
        question: La question à poser.
        mode: Mode de réponse - "synthesis" (défaut), "detailed", ou "debate".
        models: Modèles à utiliser, séparés par des virgules.
                Disponibles: claude, gpt4, gemini, mistral, cohere, deepseek, ollama.

    Returns:
        La réponse synthétisée du conseil.
    """
    logger.info("ask_conseil appelé: question=%s, mode=%s, models=%s", question[:80], mode, models)

    model_list = [m.strip() for m in models.split(",") if m.strip()]

    payload = {
        "question": question,
        "mode": mode,
        "models": model_list,
        "optimize_prompts": True,
    }

    try:
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                f"{API_URL}/api/v1/council/ask",
                json=payload,
            )
            response.raise_for_status()
            data = response.json()

        # Formater la réponse
        parts: list[str] = []

        if data.get("synthesis"):
            parts.append(data["synthesis"])

        if data.get("responses"):
            parts.append("\n---\n**Details par modele:**")
            for name, resp in data["responses"].items():
                if resp.get("error"):
                    parts.append(f"\n**{name}**: Erreur - {resp['error']}")
                else:
                    parts.append(
                        f"\n**{name}** ({resp.get('latency_ms', 0):.0f}ms, "
                        f"${resp.get('cost', 0):.4f}):\n{resp.get('content', '')[:500]}"
                    )

        meta = (
            f"\n\n---\n*Latence: {data.get('total_latency_ms', 0):.0f}ms | "
            f"Cout: ${data.get('total_cost', 0):.4f} | "
            f"Consensus: {(data.get('consensus_score') or 0) * 100:.0f}%*"
        )
        parts.append(meta)

        logger.info("Réponse conseil reçue, request_id=%s", data.get("request_id"))
        return "\n".join(parts)

    except httpx.HTTPStatusError as exc:
        logger.error("Erreur HTTP %d: %s", exc.response.status_code, exc.response.text)
        return f"Erreur API ({exc.response.status_code}): {exc.response.text}"
    except httpx.ConnectError:
        logger.error("Impossible de se connecter à %s", API_URL)
        return (
            f"Impossible de se connecter au backend ({API_URL}). "
            "Vérifiez que le serveur est lancé."
        )
    except Exception as exc:
        logger.error("Erreur inattendue: %s", exc, exc_info=True)
        return f"Erreur: {exc}"


@mcp.tool()
async def get_conseil_stats() -> str:
    """Récupère les statistiques d'utilisation du conseil.

    Returns:
        Statistiques formatées (nombre de requêtes, coûts, cache, etc.)
    """
    logger.info("get_conseil_stats appelé")

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(f"{API_URL}/api/v1/stats")
            response.raise_for_status()
            data = response.json()

        lines = [
            "**Statistiques du Conseil des IA**",
            f"- Requêtes totales: {data.get('total_requests', 0)}",
            f"- Coût total: ${data.get('total_cost', 0):.4f}",
            f"- Latence moyenne: {data.get('avg_latency_ms', 0):.0f}ms",
            f"- Taux de cache: {data.get('cache_hit_rate', 0):.1f}%",
        ]

        if data.get("requests_by_model"):
            lines.append("\n**Par modèle:**")
            for model, count in data["requests_by_model"].items():
                lines.append(f"  - {model}: {count} requêtes")

        return "\n".join(lines)

    except Exception as exc:
        logger.error("Erreur stats: %s", exc)
        return f"Erreur lors de la récupération des stats: {exc}"


@mcp.tool()
async def list_conseil_models() -> str:
    """Liste les modèles IA disponibles et leur état de configuration.

    Returns:
        Liste des modèles avec leur statut.
    """
    logger.info("list_conseil_models appelé")

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(f"{API_URL}/api/v1/models")
            response.raise_for_status()
            data = response.json()

        lines = ["**Modèles disponibles:**"]
        for model in data.get("models", []):
            status = "Configuré" if model["configured"] else "Non configuré"
            type_label = "Local" if model["type"] == "local" else "Cloud"
            lines.append(f"  - **{model['name']}** [{type_label}]: {status}")

        return "\n".join(lines)

    except Exception as exc:
        logger.error("Erreur models: %s", exc)
        return f"Erreur: {exc}"


if __name__ == "__main__":
    logger.info("Démarrage du serveur MCP Conseil des IA (API: %s)", API_URL)
    mcp.run()
