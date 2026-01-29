# Serveur MCP - Conseil des IA

Le serveur MCP permet d'utiliser le Conseil des IA directement depuis Claude Desktop ou tout client MCP compatible.

## Installation

```bash
cd mcp-server

# Creer l'environnement virtuel
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# Installer les dependances
pip install -r requirements.txt
```

## Configuration Claude Desktop

Editez le fichier de configuration de Claude Desktop :

**Linux:** `~/.config/Claude/claude_desktop_config.json`
**macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows:** `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "conseil-ia": {
      "command": "python",
      "args": ["/chemin/absolu/vers/mcp-server/server.py"],
      "env": {
        "CONSEIL_API_URL": "http://localhost:8080",
        "LOG_LEVEL": "INFO"
      }
    }
  }
}
```

## Outils disponibles

### ask_conseil

Pose une question au conseil des IA.

**Parametres :**
- `question` (string, requis) : La question a poser
- `mode` (string, defaut: "synthesis") : "synthesis", "detailed", ou "debate"
- `models` (string, defaut: "claude,gpt4,gemini") : Modeles separes par des virgules

**Exemple dans Claude Desktop :**
```
Utilise ask_conseil pour demander "Quels sont les meilleurs frameworks Python pour le web ?"
avec le mode debate et les modeles claude,gpt4,mistral
```

### get_conseil_stats

Recupere les statistiques d'utilisation.

### list_conseil_models

Liste les modeles disponibles et leur etat.

## Prerequis

Le backend doit etre lance (`uvicorn app.main:app`) pour que le serveur MCP fonctionne.

## Depannage

**"Impossible de se connecter au backend"**
- Verifiez que le backend tourne sur le bon port
- Verifiez la variable `CONSEIL_API_URL`

**Le serveur MCP n'apparait pas dans Claude Desktop**
- Verifiez le chemin absolu dans la config
- Redemarrez Claude Desktop apres modification
- Verifiez les logs : `python mcp-server/server.py` dans un terminal
