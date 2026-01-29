#!/bin/bash
# =============================================================================
# Script de déploiement GCP pour le Conseil des IA
# =============================================================================
set -euo pipefail

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

info() { echo -e "${GREEN}[INFO]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; exit 1; }

# Configuration
PROJECT_ID="${GCP_PROJECT_ID:-}"
REGION="${GCP_REGION:-europe-west1}"
BACKEND_SERVICE="conseil-ia-api"
FRONTEND_SERVICE="conseil-ia-web"

# Vérifications
command -v gcloud >/dev/null 2>&1 || error "gcloud CLI non installé. Installez-le: https://cloud.google.com/sdk/docs/install"

if [ -z "$PROJECT_ID" ]; then
    echo -n "Entrez votre GCP Project ID: "
    read -r PROJECT_ID
fi

info "Projet: $PROJECT_ID | Région: $REGION"

# Configurer le projet
gcloud config set project "$PROJECT_ID"

# Activer les APIs nécessaires
info "Activation des APIs GCP..."
gcloud services enable \
    cloudbuild.googleapis.com \
    run.googleapis.com \
    firestore.googleapis.com \
    secretmanager.googleapis.com \
    artifactregistry.googleapis.com

# Créer les secrets (si pas déjà faits)
info "Configuration des secrets..."
create_secret() {
    local name=$1
    local prompt=$2
    if ! gcloud secrets describe "$name" --project="$PROJECT_ID" >/dev/null 2>&1; then
        echo -n "$prompt: "
        read -rs value
        echo
        echo -n "$value" | gcloud secrets create "$name" --data-file=- --project="$PROJECT_ID"
        info "Secret '$name' créé"
    else
        info "Secret '$name' existe déjà"
    fi
}

create_secret "anthropic-api-key" "Clé API Anthropic (Claude)"
create_secret "openai-api-key" "Clé API OpenAI (GPT-4)"
create_secret "mistral-api-key" "Clé API Mistral (laisser vide si non utilisé)"

# Déployer le backend
info "Déploiement du backend..."
cd "$(dirname "$0")/../../backend"

gcloud run deploy "$BACKEND_SERVICE" \
    --source . \
    --region "$REGION" \
    --platform managed \
    --allow-unauthenticated \
    --port 8080 \
    --memory 512Mi \
    --cpu 1 \
    --min-instances 0 \
    --max-instances 10 \
    --set-secrets="ANTHROPIC_API_KEY=anthropic-api-key:latest,OPENAI_API_KEY=openai-api-key:latest" \
    --set-env-vars="ENVIRONMENT=production,LOG_LEVEL=INFO,LOG_FORMAT=json,GCP_PROJECT_ID=$PROJECT_ID,GCP_REGION=$REGION,CACHE_ENABLED=true"

BACKEND_URL=$(gcloud run services describe "$BACKEND_SERVICE" --region "$REGION" --format="value(status.url)")
info "Backend déployé: $BACKEND_URL"

# Déployer le frontend
info "Déploiement du frontend..."
cd "$(dirname "$0")/../../frontend"

gcloud run deploy "$FRONTEND_SERVICE" \
    --source . \
    --region "$REGION" \
    --platform managed \
    --allow-unauthenticated \
    --port 3000 \
    --memory 256Mi \
    --cpu 1 \
    --min-instances 0 \
    --max-instances 5 \
    --set-env-vars="NEXT_PUBLIC_API_URL=$BACKEND_URL"

FRONTEND_URL=$(gcloud run services describe "$FRONTEND_SERVICE" --region "$REGION" --format="value(status.url)")

echo ""
info "=========================================="
info "  Déploiement terminé !"
info "=========================================="
info "Backend  : $BACKEND_URL"
info "Frontend : $FRONTEND_URL"
info "API Docs : $BACKEND_URL/docs"
info "Health   : $BACKEND_URL/api/v1/health"
echo ""
