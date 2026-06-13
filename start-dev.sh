#!/bin/bash
# Lance le backend ET le frontend en développement.
# Usage : bash start-dev.sh

cd "$(dirname "$0")"

echo "=== NeoTechno Trading Bot — DEV ==="
echo ""

# Copie le .env si absent
if [ ! -f .env ]; then
  cp .env.example .env
  echo "📄 .env créé depuis .env.example — vérifie les variables si besoin."
fi

echo "🖥️  Backend  → http://localhost:3001"
echo "🌐 Frontend → http://localhost:3000"
echo ""

# Lance le backend en arrière-plan
(cd backend && node app.js) &
BACKEND_PID=$!

# Lance le frontend en foreground
(cd frontend && npm run dev)

# Arrête le backend quand le frontend s'arrête
kill $BACKEND_PID 2>/dev/null
