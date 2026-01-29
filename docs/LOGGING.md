# Systeme de Logging - Conseil des IA

## Architecture

Le systeme de logging est concu pour la production avec support complet des 5 niveaux standard.

### Niveaux de log

| Niveau | Code | Usage | Exemple |
|--------|------|-------|---------|
| **CRITICAL** | 50 | Erreur fatale, service inutilisable | Impossible de demarrer, config invalide |
| **ERROR** | 40 | Erreur recuperable | Un modele IA echoue, Firestore indisponible |
| **WARNING** | 30 | Situation anormale mais geree | Cache miss, timeout proche, cle API manquante |
| **INFO** | 20 | Evenement metier normal | Requete recue, reponse envoyee, demarrage |
| **DEBUG** | 10 | Detail technique | Payloads, timings internes, etats intermediaires |

### Formats de sortie

**Developpement (`LOG_FORMAT=text`):**
```
2026-01-29 14:30:00.123 [INFO    ] conseil_ia.api.routes:ask_council:85 - Requete /council/ask recue
2026-01-29 14:30:02.456 [DEBUG   ] conseil_ia.models.claude:generate:45 - Envoi requete Claude
2026-01-29 14:30:03.789 [INFO    ] conseil_ia.models.base:safe_generate:92 - Reponse recue de claude en 1333ms
```

**Production (`LOG_FORMAT=json`):**
```json
{
  "timestamp": "2026-01-29T14:30:00.123Z",
  "level": "INFO",
  "severity": "INFO",
  "logger": "conseil_ia.api.routes",
  "message": "Requete /council/ask recue",
  "module": "routes",
  "function": "ask_council",
  "line": 85,
  "request_id": "a1b2c3d4",
  "data": {
    "mode": "synthesis",
    "models": ["claude", "gpt4"],
    "question_preview": "Explique..."
  }
}
```

### Configuration

Dans `backend/.env` :
```env
LOG_LEVEL=DEBUG          # Niveau minimum a logger
LOG_FORMAT=text          # "text" (dev) ou "json" (prod)
LOG_FILE=logs/app.log    # Optionnel, fichier de log
```

### Contexte de requete

Chaque requete HTTP recoit un `request_id` unique, propage dans tous les logs de cette requete. Cela permet de tracer une requete complete dans les logs.

Headers de reponse :
- `X-Request-ID` : ID unique de la requete
- `X-Response-Time` : Temps de traitement

### Composants logges

| Composant | Logger | Ce qui est logge |
|-----------|--------|-----------------|
| Middleware HTTP | `conseil_ia.middleware.request` | Methode, path, status, latence |
| Rate limiter | `conseil_ia.middleware.rate_limiter` | Depassements de limite |
| Routes API | `conseil_ia.api.routes` | Requetes recues, erreurs |
| Orchestrateur | `conseil_ia.services.orchestrator` | Workflow complet, stats |
| Cache | `conseil_ia.services.cache` | Hit/miss, TTL, stats |
| Synthese | `conseil_ia.services.synthesis` | Consensus, mode |
| Modeles IA | `conseil_ia.models.*` | Appels, latences, erreurs, couts |

### Librairies tierces

Les logs des librairies tierces sont reduits au niveau WARNING pour eviter le bruit :
- httpx, httpcore, uvicorn.access, google, urllib3

### Compatibilite

Le format JSON est compatible avec :
- Google Cloud Logging (champ `severity`)
- ELK Stack (Elasticsearch, Logstash, Kibana)
- Datadog
- Grafana Loki
