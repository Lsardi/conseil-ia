"""Service de cache pour les réponses du conseil.

Supporte deux backends :
- Firestore (production, GCP)
- In-memory (développement local, pas de dépendance externe)
"""

from __future__ import annotations

import hashlib
import json
import time
from typing import Any, Optional

from ..config.logging_config import get_logger
from ..config.settings import get_settings

logger = get_logger("services.cache")


class CacheService:
    """Service de cache dual : mémoire locale + Firestore optionnel."""

    def __init__(self) -> None:
        settings = get_settings()
        self._ttl = settings.cache_ttl
        self._enabled = settings.cache_enabled
        self._collection_name = settings.firestore_collection

        # Cache mémoire local (toujours actif)
        self._memory_cache: dict[str, dict[str, Any]] = {}

        # Firestore (optionnel)
        self._firestore_db = None
        self._firestore_available = False

        # Statistiques
        self._hits = 0
        self._misses = 0

        if self._enabled:
            self._init_firestore()

    def _init_firestore(self) -> None:
        """Tente d'initialiser Firestore. Échoue silencieusement."""
        try:
            from google.cloud import firestore

            self._firestore_db = firestore.AsyncClient()
            self._firestore_available = True
            logger.info("Cache Firestore initialisé")
        except Exception as exc:
            logger.warning(
                "Firestore non disponible, utilisation du cache mémoire uniquement: %s",
                exc,
            )
            self._firestore_available = False

    @staticmethod
    def _make_key(question: str, models: list[str], mode: str) -> str:
        """Génère une clé de cache déterministe."""
        payload = json.dumps(
            {"question": question.strip().lower(), "models": sorted(models), "mode": mode},
            sort_keys=True,
        )
        return hashlib.sha256(payload.encode()).hexdigest()

    async def get(
        self, question: str, models: list[str], mode: str
    ) -> Optional[dict[str, Any]]:
        """Cherche une entrée dans le cache.

        Args:
            question: La question posée.
            models: Les modèles interrogés.
            mode: Le mode de réponse.

        Returns:
            Les données cachées ou None.
        """
        if not self._enabled:
            return None

        key = self._make_key(question, models, mode)

        # 1. Check mémoire locale
        if key in self._memory_cache:
            entry = self._memory_cache[key]
            if time.time() - entry["timestamp"] < self._ttl:
                self._hits += 1
                logger.debug(
                    "Cache HIT (mémoire) pour clé %s",
                    key[:12],
                    extra={"extra_data": {"cache_key": key, "source": "memory"}},
                )
                return entry["data"]
            else:
                del self._memory_cache[key]
                logger.debug("Cache EXPIRED (mémoire) pour clé %s", key[:12])

        # 2. Check Firestore
        if self._firestore_available and self._firestore_db:
            try:
                doc_ref = self._firestore_db.collection(self._collection_name).document(
                    key
                )
                doc = await doc_ref.get()
                if doc.exists:
                    data = doc.to_dict()
                    if data and time.time() - data.get("timestamp", 0) < self._ttl:
                        # Remplir le cache mémoire
                        self._memory_cache[key] = data
                        self._hits += 1
                        logger.debug(
                            "Cache HIT (Firestore) pour clé %s",
                            key[:12],
                            extra={
                                "extra_data": {"cache_key": key, "source": "firestore"}
                            },
                        )
                        return data.get("data")
            except Exception as exc:
                logger.warning("Erreur lecture Firestore: %s", exc)

        self._misses += 1
        logger.debug("Cache MISS pour clé %s", key[:12])
        return None

    async def set(
        self,
        question: str,
        models: list[str],
        mode: str,
        data: dict[str, Any],
    ) -> None:
        """Stocke une entrée dans le cache.

        Args:
            question: La question posée.
            models: Les modèles interrogés.
            mode: Le mode de réponse.
            data: Les données à cacher.
        """
        if not self._enabled:
            return

        key = self._make_key(question, models, mode)
        entry = {"data": data, "timestamp": time.time(), "question": question}

        # 1. Mémoire locale
        self._memory_cache[key] = entry
        logger.debug("Cache SET (mémoire) pour clé %s", key[:12])

        # 2. Firestore
        if self._firestore_available and self._firestore_db:
            try:
                doc_ref = self._firestore_db.collection(self._collection_name).document(
                    key
                )
                await doc_ref.set(entry)
                logger.debug("Cache SET (Firestore) pour clé %s", key[:12])
            except Exception as exc:
                logger.warning("Erreur écriture Firestore: %s", exc)

    @property
    def hit_rate(self) -> float:
        """Retourne le taux de cache hit en pourcentage."""
        total = self._hits + self._misses
        if total == 0:
            return 0.0
        return (self._hits / total) * 100

    @property
    def stats(self) -> dict[str, Any]:
        """Retourne les statistiques du cache."""
        return {
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": round(self.hit_rate, 2),
            "memory_entries": len(self._memory_cache),
            "firestore_available": self._firestore_available,
            "enabled": self._enabled,
        }

    async def clear(self) -> None:
        """Vide le cache mémoire."""
        self._memory_cache.clear()
        self._hits = 0
        self._misses = 0
        logger.info("Cache mémoire vidé")
