# API Reference - Conseil des IA

Base URL: `http://localhost:8080` (dev) ou votre URL Cloud Run (prod)

Documentation interactive: `{BASE_URL}/docs` (Swagger UI)

## Endpoints

### POST /api/v1/council/ask

Interroge le conseil des IA.

**Request Body:**

| Champ | Type | Defaut | Description |
|-------|------|--------|-------------|
| `question` | string (requis) | - | Question a poser (1-10000 car.) |
| `mode` | string | `"synthesis"` | `synthesis`, `detailed`, ou `debate` |
| `models` | string[] | `["claude","gpt4","gemini"]` | Modeles a utiliser |
| `optimize_prompts` | boolean | `true` | Optimiser les prompts par modele |
| `temperature` | float | `0.7` | Creativite (0.0-2.0) |
| `max_tokens` | int | `4000` | Tokens max par reponse (1-16000) |
| `stream` | boolean | `false` | Streaming (a venir) |
| `user_id` | string | `null` | ID utilisateur pour tracking |

**Exemple:**

```bash
curl -X POST http://localhost:8080/api/v1/council/ask \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Quels sont les avantages de Rust vs Go ?",
    "mode": "debate",
    "models": ["claude", "gpt4", "mistral"],
    "temperature": 0.8
  }'
```

**Response (200):**

```json
{
  "synthesis": "## Debat du Conseil des IA\n...",
  "responses": {
    "claude": {
      "model": "claude",
      "content": "Rust offre...",
      "tokens_input": 150,
      "tokens_output": 450,
      "latency_ms": 2340.5,
      "cost": 0.0082,
      "error": null,
      "cached": false
    },
    "gpt4": { ... },
    "mistral": { ... }
  },
  "consensus_score": 0.62,
  "total_cost": 0.0234,
  "total_latency_ms": 3500.2,
  "cached": false,
  "mode": "debate",
  "request_id": "a1b2c3d4"
}
```

### GET /api/v1/models

Liste les modeles disponibles.

```json
{
  "models": [
    { "name": "claude", "configured": true, "type": "cloud" },
    { "name": "gpt4", "configured": true, "type": "cloud" },
    { "name": "gemini", "configured": false, "type": "cloud" },
    { "name": "mistral", "configured": true, "type": "cloud" },
    { "name": "cohere", "configured": false, "type": "cloud" },
    { "name": "deepseek", "configured": false, "type": "cloud" },
    { "name": "ollama", "configured": true, "type": "local" }
  ]
}
```

### GET /api/v1/stats

```json
{
  "total_requests": 42,
  "total_cost": 0.84,
  "cache_hit_rate": 38.5,
  "avg_latency_ms": 3200.0,
  "requests_by_model": { "claude": 42, "gpt4": 40, "gemini": 38 },
  "requests_by_mode": { "synthesis": 30, "debate": 8, "detailed": 4 }
}
```

### GET /api/v1/health

```json
{
  "status": "healthy",
  "version": "1.0.0",
  "environment": "development",
  "models_configured": {
    "claude": true,
    "gpt4": true,
    "gemini": false,
    "mistral": false,
    "cohere": false,
    "deepseek": false,
    "ollama": false
  },
  "cache_enabled": true
}
```

## Codes d'erreur

| Code | Description |
|------|-------------|
| 200 | Succes |
| 422 | Erreur de validation (champs invalides) |
| 429 | Rate limit depasse (20 req/min par defaut) |
| 500 | Erreur serveur |

## Headers de reponse

| Header | Description |
|--------|-------------|
| `X-Request-ID` | Identifiant unique de la requete |
| `X-Response-Time` | Temps de traitement (ex: "3500ms") |
