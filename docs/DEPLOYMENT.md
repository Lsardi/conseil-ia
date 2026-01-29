# Guide de deploiement - Conseil des IA

## Option 1 : Local (developpement)

### Prerequis
- Python 3.11+
- Node.js 18+
- (Optionnel) Ollama pour les modeles locaux

### Installation

```bash
# Cloner le projet
git clone https://github.com/VOTRE_USER/conseil-ia.git
cd conseil-ia

# Installation automatique
chmod +x install.sh
./install.sh

# Configurer les cles API
nano backend/.env
```

### Lancement

```bash
# Terminal 1 - Backend
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --log-level debug

# Terminal 2 - Frontend
cd frontend
npm run dev
```

### Avec Ollama (modeles locaux)

```bash
# Installer Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Telecharger un modele
ollama pull llama3.1
ollama pull mistral

# Activer dans backend/.env
OLLAMA_ENABLED=true
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1
```

## Option 2 : Docker Compose

```bash
# Configuration
cp backend/.env.example backend/.env
# Editer backend/.env

# Lancer backend + frontend
docker-compose up -d

# Avec Ollama en plus
docker-compose --profile local up -d

# Logs
docker-compose logs -f backend
docker-compose logs -f frontend
```

## Option 3 : Google Cloud Platform

### Prerequis GCP
- Compte GCP avec facturation activee
- gcloud CLI installe
- Droits Owner ou Editor sur le projet

### Deploiement automatique

```bash
cd deployment/scripts
chmod +x deploy.sh

# Le script vous guide a travers :
# 1. Configuration du projet GCP
# 2. Activation des APIs
# 3. Creation des secrets (cles API)
# 4. Deploiement Cloud Run (backend + frontend)
./deploy.sh
```

### Deploiement manuel

```bash
# 1. Configurer gcloud
gcloud auth login
gcloud config set project VOTRE_PROJET

# 2. Activer les APIs
gcloud services enable \
    cloudbuild.googleapis.com \
    run.googleapis.com \
    firestore.googleapis.com \
    secretmanager.googleapis.com

# 3. Creer les secrets
echo "votre-cle" | gcloud secrets create anthropic-api-key --data-file=-
echo "votre-cle" | gcloud secrets create openai-api-key --data-file=-

# 4. Deployer le backend
cd backend
gcloud run deploy conseil-ia-api \
    --source . \
    --region europe-west1 \
    --allow-unauthenticated \
    --port 8080 \
    --set-secrets="ANTHROPIC_API_KEY=anthropic-api-key:latest,OPENAI_API_KEY=openai-api-key:latest" \
    --set-env-vars="ENVIRONMENT=production,LOG_FORMAT=json"

# 5. Deployer le frontend
cd ../frontend
gcloud run deploy conseil-ia-web \
    --source . \
    --region europe-west1 \
    --allow-unauthenticated \
    --port 3000 \
    --set-env-vars="NEXT_PUBLIC_API_URL=https://conseil-ia-api-XXXX.run.app"
```

### CI/CD avec Cloud Build

Le fichier `deployment/cloudbuild.yaml` configure un pipeline qui :
1. Execute les tests backend
2. Build les images Docker
3. Deploie sur Cloud Run

Pour activer :
```bash
gcloud builds triggers create github \
    --repo-name=conseil-ia \
    --branch-pattern=^main$ \
    --build-config=deployment/cloudbuild.yaml
```

## Monitoring (GCP)

```bash
# Logs en temps reel
gcloud run logs tail conseil-ia-api --region=europe-west1

# Metriques
# Voir Cloud Console > Cloud Run > conseil-ia-api > Metrics
```

## Couts estimes

### Infrastructure GCP
| Service | Cout mensuel |
|---------|-------------|
| Cloud Run (backend) | $10-30 |
| Cloud Run (frontend) | $5-15 |
| Firestore | $1-5 |
| **Total** | **$15-50/mois** |

### API par requete
| Config | Cout |
|--------|------|
| Claude + GPT-4 + Gemini | ~$0.02 |
| Avec cache (40% hit) | ~$0.012 |
| Ollama uniquement | $0.00 |
