"""Service de synthèse des réponses multi-modèles.

Combine les réponses de plusieurs IA en une synthèse cohérente
et calcule un score de consensus.
"""

from __future__ import annotations

from ..config.logging_config import get_logger
from ..models.base import ModelResult

logger = get_logger("services.synthesis")


class SynthesisService:
    """Synthétise les réponses de plusieurs modèles IA."""

    async def synthesize(
        self,
        question: str,
        results: dict[str, ModelResult],
    ) -> str:
        """Crée une synthèse unifiée des réponses.

        Args:
            question: La question originale.
            results: Dict {model_name: ModelResult} des réponses.

        Returns:
            Texte de synthèse.
        """
        valid_results = {
            name: r for name, r in results.items() if r.content and not r.error
        }

        if not valid_results:
            logger.warning("Aucune réponse valide pour la synthèse")
            return "Aucun modèle n'a pu fournir de réponse valide."

        if len(valid_results) == 1:
            name, result = next(iter(valid_results.items()))
            logger.info("Synthèse avec un seul modèle: %s", name)
            return f"**Réponse de {name}:**\n\n{result.content}"

        # Construire la synthèse structurée
        parts: list[str] = []
        parts.append(f"## Synthèse du Conseil des IA\n")
        parts.append(f"**Question:** {question}\n")
        parts.append(f"**Modèles consultés:** {', '.join(valid_results.keys())}\n")
        parts.append("---\n")

        # Points clés de chaque modèle
        parts.append("### Points clés par modèle\n")
        for name, result in valid_results.items():
            # Extraire un résumé (premiers 500 caractères)
            summary = result.content[:500]
            if len(result.content) > 500:
                summary += "..."
            parts.append(f"**{name}:** {summary}\n")

        # Consensus
        consensus = self.calculate_consensus(valid_results)
        parts.append(f"\n### Consensus: {consensus:.0%}\n")

        if consensus > 0.7:
            parts.append(
                "Les modèles sont largement en accord sur les points principaux.\n"
            )
        elif consensus > 0.4:
            parts.append(
                "Les modèles présentent des perspectives complémentaires "
                "avec des points de convergence.\n"
            )
        else:
            parts.append(
                "Les modèles divergent significativement. "
                "Consultez les réponses individuelles pour plus de détails.\n"
            )

        logger.info(
            "Synthèse générée",
            extra={
                "extra_data": {
                    "models_count": len(valid_results),
                    "consensus": consensus,
                }
            },
        )

        return "\n".join(parts)

    async def create_debate(
        self,
        question: str,
        results: dict[str, ModelResult],
    ) -> str:
        """Crée un format débat entre les modèles.

        Args:
            question: La question originale.
            results: Dict {model_name: ModelResult} des réponses.

        Returns:
            Texte du débat formaté.
        """
        valid_results = {
            name: r for name, r in results.items() if r.content and not r.error
        }

        if not valid_results:
            return "Aucun modèle n'a pu participer au débat."

        parts: list[str] = []
        parts.append(f"## Débat du Conseil des IA\n")
        parts.append(f"**Sujet:** {question}\n")
        parts.append(f"**Participants:** {', '.join(valid_results.keys())}\n")
        parts.append("---\n")

        for name, result in valid_results.items():
            parts.append(f"### {name}\n")
            parts.append(f"{result.content}\n")
            parts.append("---\n")

        # Analyse des divergences
        consensus = self.calculate_consensus(valid_results)
        parts.append(f"\n### Analyse du débat\n")
        parts.append(f"**Score de consensus:** {consensus:.0%}\n")

        if consensus > 0.7:
            parts.append("**Verdict:** Les participants convergent largement.\n")
        elif consensus > 0.4:
            parts.append(
                "**Verdict:** Perspectives complémentaires avec des nuances.\n"
            )
        else:
            parts.append(
                "**Verdict:** Positions divergentes — la question mérite "
                "une analyse approfondie.\n"
            )

        logger.info(
            "Débat généré",
            extra={
                "extra_data": {
                    "models_count": len(valid_results),
                    "consensus": consensus,
                }
            },
        )

        return "\n".join(parts)

    @staticmethod
    def calculate_consensus(results: dict[str, ModelResult]) -> float:
        """Calcule un score de consensus entre les réponses.

        Utilise la similarité lexicale (Jaccard) comme approximation simple.
        Pour une version production, utiliser des embeddings.

        Args:
            results: Dict {model_name: ModelResult}.

        Returns:
            Score entre 0.0 (aucun accord) et 1.0 (accord total).
        """
        if len(results) < 2:
            return 1.0

        contents = [r.content.lower() for r in results.values() if r.content]
        if len(contents) < 2:
            return 1.0

        # Tokenisation simple
        word_sets = [set(c.split()) for c in contents]

        # Calculer la similarité de Jaccard moyenne entre toutes les paires
        similarities: list[float] = []
        for i in range(len(word_sets)):
            for j in range(i + 1, len(word_sets)):
                intersection = word_sets[i] & word_sets[j]
                union = word_sets[i] | word_sets[j]
                if union:
                    similarities.append(len(intersection) / len(union))

        if not similarities:
            return 0.0

        return sum(similarities) / len(similarities)
