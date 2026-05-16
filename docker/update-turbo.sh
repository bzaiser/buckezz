#!/bin/bash

# Exit on any error
set -e

# Find the script's directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

echo "🚀 Starte TURBO Update (Nur Code/Design, kein Restart)..."

# Move to the project root directory
cd "$ROOT_DIR"

# Pull new changes from git
echo "⏬ Pulling from git..."
git pull origin $(git rev-parse --abbrev-ref HEAD)

# Permissions
echo "🔐 Setze Berechtigungen..."
chmod -R a+rwX .
chmod +x manage.py

# Collect static
echo "🎨 Sammle statische Dateien..."
docker compose exec web python manage.py collectstatic --noinput

echo "-----------------------------------"
echo "⚡ TURBO Update abgeschlossen! Änderungen sind sofort live."
