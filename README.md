# Conseil des IA - Plateforme Multi-Modele Intelligente

Plateforme qui interroge simultanement **7 modeles IA** (Claude, GPT-4, Gemini, Mistral, Cohere, DeepSeek + Ollama local), optimise les prompts pour chaque modele, et synthetise leurs reponses.

## Fonctionnalites

- **7 modeles IA** : Claude Sonnet 4, GPT-4o, Gemini 2.0 Flash, Mistral Large, Cohere Command R+, DeepSeek Chat, Ollama (local)
- **Mode local** : Ollama pour executer des LLM sans cout API (Llama 3, Mistral, Phi, etc.)
- **3 modes de reponse** : Synthese, Detail, Debat
- **Optimisation des prompts** : Adapte automatiquement les prompts pour chaque modele
- **Cache intelligent** : Memoire + Firestore (taux de hit ~40%)
- **API REST** : Documentation Swagger automatique
- **PWA** : Application web installable sur mobile et desktop
- **Serveur MCP** : Integration directe avec Claude Desktop
- **Logging production** : JSON structure, tous niveaux (DEBUG a CRITICAL)
- **Deploiement GCP** : Cloud Run, Cloud Build CI/CD

## Architecture

```
conseil-ia-project/
├── backend/                 # API FastAPI (Python 3.11+)
│   ├── app/
│   │   ├── models/         # Adaptateurs IA (7 modeles)
│   │   ├── services/       # Orchestrateur, cache, synthese
│   │   ├── api/            # Endpoints REST
│   │   ├── middleware/      # Logging, rate limiting
│   │   └── config/         # Settings, schemas, logging
│   ├── tests/              # Tests unitaires
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/               # Next.js + Tailwind CSS (PWA)
│   ├── pages/
│   ├── components/
│   ├── lib/
│   └── Dockerfile
├── mcp-server/             # Serveur MCP pour Claude Desktop
├── deployment/             # Scripts GCP + Cloud Build
├── docker-compose.yml      # Lancement local complet
└── install.sh              # Installation automatique
```

## Demarrage rapide

### Prerequis

- Python 3.11+
- Node.js 18+ (pour le frontend)
- Au moins une cle API (Anthropic, OpenAI, ou autre)
- Ollama (optionnel, pour les modeles locaux)

### Installation

```bash
git clone https://github.com/VOTRE_USER/conseil-ia.git
cd conseil-ia

# Installation automatique
chmod +x install.sh
./install.sh
```

### Lancement

**Terminal 1 - Backend :**
```bash
cd backend
source venv/bin/activate    # Linux/Mac
# ou: venv\Scripts\activate  # Windows
uvicorn app.main:app --reload
```

**Terminal 2 - Frontend :**
```bash
cd frontend
npm run dev
```

**Acces :**
- Application web : http://localhost:3000
- API Documentation : http://localhost:8080/docs
- Health check : http://localhost:8080/api/v1/health

### Avec Docker Compose

```bash
# Copier la config
cp backend/.env.example backend/.env
# Editer backend/.env avec vos cles API

# Lancer
docker-compose up -d

# Avec Ollama (modeles locaux)
docker-compose --profile local up -d
```

## Configuration

Editez `backend/.env` :

```env
# Cles API (remplissez celles que vous avez)
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
MISTRAL_API_KEY=
COHERE_API_KEY=
DEEPSEEK_API_KEY=

# Modeles locaux (Ollama)
OLLAMA_ENABLED=false
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1

# Logging
LOG_LEVEL=DEBUG        # DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_FORMAT=text        # "text" (dev) ou "json" (prod)
```

### Ou obtenir les cles API

| Service | URL | Modele |
|---------|-----|--------|
| Anthropic (Claude) | https://console.anthropic.com/ | claude-sonnet-4 |
| OpenAI (GPT-4) | https://platform.openai.com/api-keys | gpt-4o |
| Google (Gemini) | https://console.cloud.google.com/ | gemini-2.0-flash |
| Mistral | https://console.mistral.ai/ | mistral-large-latest |
| Cohere | https://dashboard.cohere.com/api-keys | command-r-plus |
| DeepSeek | https://platform.deepseek.com/ | deepseek-chat |
| Ollama (local) | https://ollama.ai/ | llama3.1, mistral, phi3... |

### Installation Ollama (modeles locaux)

```bash
# Installer Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Telecharger un modele
ollama pull llama3.1

# Activer dans .env
OLLAMA_ENABLED=true
```

## API

### POST /api/v1/council/ask

```bash
curl -X POST http://localhost:8080/api/v1/council/ask \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Explique la theorie de la relativite",
    "mode": "synthesis",
    "models": ["claude", "gpt4", "gemini"],
    "optimize_prompts": true,
    "temperature": 0.7
  }'
```

**Modes :** `synthesis` (defaut), `detailed`, `debate`

**Modeles :** `claude`, `gpt4`, `gemini`, `mistral`, `cohere`, `deepseek`, `ollama`

### GET /api/v1/models

Liste les modeles disponibles et leur etat de configuration.

### GET /api/v1/stats

Statistiques d'utilisation (requetes, couts, cache).

### GET /api/v1/health

Health check du service.

## Serveur MCP

Pour utiliser le conseil dans Claude Desktop :

```bash
cd mcp-server
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Editez `~/.config/Claude/claude_desktop_config.json` :

```json
{
  "mcpServers": {
    "conseil-ia": {
      "command": "python",
      "args": ["/chemin/absolu/vers/mcp-server/server.py"],
      "env": {
        "CONSEIL_API_URL": "http://localhost:8080"
      }
    }
  }
}
```

Outils MCP disponibles :
- `ask_conseil` : Poser une question au conseil
- `get_conseil_stats` : Statistiques d'utilisation
- `list_conseil_models` : Lister les modeles

## Deploiement GCP

```bash
cd deployment/scripts
chmod +x deploy.sh
./deploy.sh
```

Le script active les APIs, cree les secrets, et deploie sur Cloud Run.

## Tests

```bash
cd backend
source venv/bin/activate
pytest tests/ -v
```

## Logging

Le systeme de logging couvre 5 niveaux :

| Niveau | Usage |
|--------|-------|
| **CRITICAL** | Erreur fatale empechant le fonctionnement |
| **ERROR** | Erreur recuperable (modele IA echoue, etc.) |
| **WARNING** | Situation anormale geree (cache miss, timeout) |
| **INFO** | Evenement metier normal (requete, reponse) |
| **DEBUG** | Detail technique (payloads, timings) |

En production : JSON structure compatible Cloud Logging.
En developpement : Texte colore lisible.

## Couts estimes

| Modele | Cout/requete |
|--------|-------------|
| Claude Sonnet 4 | ~$0.003 |
| GPT-4o | ~$0.015 |
| Gemini 2.0 Flash | ~$0.001 |
| Mistral Large | ~$0.006 |
| Cohere Command R+ | ~$0.002 |
| DeepSeek Chat | ~$0.003 |
| Ollama (local) | $0.000 |

## Licence

MIT
