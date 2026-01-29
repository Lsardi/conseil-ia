#!/bin/bash
# =============================================================================
# Script d'installation locale du Conseil des IA
# =============================================================================
set -euo pipefail

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

info() { echo -e "${GREEN}[OK]${NC} $1"; }
warn() { echo -e "${YELLOW}[!]${NC} $1"; }
error() { echo -e "${RED}[ERREUR]${NC} $1"; }

echo ""
echo "=========================================="
echo "  Installation du Conseil des IA"
echo "=========================================="
echo ""

# Vérifier Python
if command -v python3 &>/dev/null; then
    PYTHON=python3
    info "Python3 trouvé: $(python3 --version)"
elif command -v python &>/dev/null; then
    PYTHON=python
    info "Python trouvé: $(python --version)"
else
    error "Python 3.11+ requis. Installez-le depuis https://python.org"
    exit 1
fi

# Vérifier Node.js
if command -v node &>/dev/null; then
    info "Node.js trouvé: $(node --version)"
else
    warn "Node.js non trouvé. Le frontend ne sera pas installé."
    warn "Installez Node.js 18+ depuis https://nodejs.org"
fi

# --- Backend ---
echo ""
info "Installation du backend..."
cd backend

if [ ! -d "venv" ]; then
    $PYTHON -m venv venv
    info "Environnement virtuel créé"
fi

source venv/bin/activate 2>/dev/null || source venv/Scripts/activate 2>/dev/null
pip install -q -r requirements.txt
info "Dépendances Python installées"

if [ ! -f ".env" ]; then
    cp .env.example .env
    warn "Fichier .env créé. Éditez-le avec vos clés API !"
else
    info "Fichier .env existant conservé"
fi

cd ..

# --- Frontend ---
if command -v node &>/dev/null; then
    echo ""
    info "Installation du frontend..."
    cd frontend
    npm install --silent
    info "Dépendances Node.js installées"

    if [ ! -f ".env.local" ]; then
        echo "NEXT_PUBLIC_API_URL=http://localhost:8080" > .env.local
        info "Fichier .env.local créé"
    fi
    cd ..
fi

# --- MCP Server ---
echo ""
info "Installation du serveur MCP..."
cd mcp-server
if [ ! -d "venv" ]; then
    $PYTHON -m venv venv
fi
source venv/bin/activate 2>/dev/null || source venv/Scripts/activate 2>/dev/null
pip install -q -r requirements.txt
info "Dépendances MCP installées"
cd ..

echo ""
echo "=========================================="
echo -e "  ${GREEN}Installation terminée !${NC}"
echo "=========================================="
echo ""
echo "Pour lancer le projet :"
echo ""
echo "  Terminal 1 (Backend) :"
echo "    cd backend"
echo "    source venv/bin/activate"
echo "    uvicorn app.main:app --reload"
echo ""
echo "  Terminal 2 (Frontend) :"
echo "    cd frontend"
echo "    npm run dev"
echo ""
echo "  Accès :"
echo "    - Application : http://localhost:3000"
echo "    - API Docs    : http://localhost:8080/docs"
echo "    - Health      : http://localhost:8080/api/v1/health"
echo ""
echo -e "  ${YELLOW}N'oubliez pas d'éditer backend/.env avec vos clés API !${NC}"
echo ""
