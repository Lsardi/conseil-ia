"""Configuration du logging production-grade.

Niveaux de log utilisés :
- CRITICAL : Erreurs fatales empêchant le fonctionnement du service
- ERROR    : Erreurs récupérables (ex: un modèle IA échoue, mais les autres répondent)
- WARNING  : Situations anormales mais gérées (ex: cache miss, timeout proche)
- INFO     : Événements métier normaux (ex: requête reçue, réponse envoyée)
- DEBUG    : Détails techniques pour le debugging (ex: payloads, timings internes)
"""

from __future__ import annotations

import json
import logging
import sys
import traceback
from datetime import datetime, timezone
from typing import Any, Optional

from .settings import Environment, LogLevel, get_settings


class JSONFormatter(logging.Formatter):
    """Formatter JSON structuré pour les environnements de production.

    Produit des logs compatibles avec Cloud Logging, ELK, Datadog, etc.
    """

    def format(self, record: logging.LogRecord) -> str:
        log_entry: dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(
                record.created, tz=timezone.utc
            ).isoformat(),
            "level": record.levelname,
            "severity": record.levelname,  # Compatibilité Cloud Logging
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Ajouter le contexte de la requête si disponible
        if hasattr(record, "request_id"):
            log_entry["request_id"] = record.request_id
        if hasattr(record, "user_id"):
            log_entry["user_id"] = record.user_id
        if hasattr(record, "trace_id"):
            log_entry["logging.googleapis.com/trace"] = record.trace_id

        # Ajouter les extras personnalisés
        if hasattr(record, "extra_data"):
            log_entry["data"] = record.extra_data

        # Ajouter l'exception si présente
        if record.exc_info and record.exc_info[0] is not None:
            log_entry["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "stacktrace": traceback.format_exception(*record.exc_info),
            }

        return json.dumps(log_entry, ensure_ascii=False, default=str)


class TextFormatter(logging.Formatter):
    """Formatter lisible pour le développement local."""

    COLORS = {
        "DEBUG": "\033[36m",      # Cyan
        "INFO": "\033[32m",       # Vert
        "WARNING": "\033[33m",    # Jaune
        "ERROR": "\033[31m",      # Rouge
        "CRITICAL": "\033[1;31m", # Rouge gras
    }
    RESET = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:
        color = self.COLORS.get(record.levelname, self.RESET)
        timestamp = datetime.fromtimestamp(
            record.created, tz=timezone.utc
        ).strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]

        base = (
            f"{color}{timestamp} "
            f"[{record.levelname:<8}] "
            f"{record.name}:{record.funcName}:{record.lineno} "
            f"- {record.getMessage()}{self.RESET}"
        )

        if hasattr(record, "extra_data"):
            base += f" | data={record.extra_data}"

        if record.exc_info and record.exc_info[0] is not None:
            base += "\n" + "".join(traceback.format_exception(*record.exc_info))

        return base


class RequestContextFilter(logging.Filter):
    """Filtre qui injecte le contexte de la requête dans chaque log."""

    def __init__(self) -> None:
        super().__init__()
        self._request_id: Optional[str] = None
        self._user_id: Optional[str] = None
        self._trace_id: Optional[str] = None

    def set_context(
        self,
        request_id: Optional[str] = None,
        user_id: Optional[str] = None,
        trace_id: Optional[str] = None,
    ) -> None:
        self._request_id = request_id
        self._user_id = user_id
        self._trace_id = trace_id

    def clear_context(self) -> None:
        self._request_id = None
        self._user_id = None
        self._trace_id = None

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = self._request_id  # type: ignore[attr-defined]
        record.user_id = self._user_id  # type: ignore[attr-defined]
        record.trace_id = self._trace_id  # type: ignore[attr-defined]
        return True


# Instance globale du filtre de contexte
request_context_filter = RequestContextFilter()


def setup_logging() -> None:
    """Configure le système de logging pour toute l'application.

    - En production : JSON structuré vers stdout (compatible Cloud Logging)
    - En développement : Texte coloré lisible
    - Fichier de log optionnel
    """
    settings = get_settings()

    # Niveau de log racine
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, settings.log_level.value))

    # Supprimer les handlers existants
    root_logger.handlers.clear()

    # Choisir le formatter
    if settings.log_format == "json" or settings.environment == Environment.PRODUCTION:
        formatter = JSONFormatter()
    else:
        formatter = TextFormatter()

    # Handler stdout
    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setFormatter(formatter)
    stdout_handler.addFilter(request_context_filter)
    root_logger.addHandler(stdout_handler)

    # Handler fichier optionnel
    if settings.log_file:
        file_handler = logging.FileHandler(settings.log_file, encoding="utf-8")
        file_handler.setFormatter(JSONFormatter())  # Toujours JSON en fichier
        file_handler.addFilter(request_context_filter)
        root_logger.addHandler(file_handler)

    # Réduire le bruit des librairies tierces
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("google").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)

    # Log de démarrage
    logger = logging.getLogger("conseil_ia.startup")
    logger.info(
        "Logging configuré",
        extra={
            "extra_data": {
                "environment": settings.environment.value,
                "log_level": settings.log_level.value,
                "log_format": settings.log_format,
                "log_file": settings.log_file,
            }
        },
    )


def get_logger(name: str) -> logging.Logger:
    """Retourne un logger nommé avec le préfixe du projet.

    Args:
        name: Nom du module (ex: 'orchestrator', 'models.claude').

    Returns:
        Logger configuré.
    """
    return logging.getLogger(f"conseil_ia.{name}")
