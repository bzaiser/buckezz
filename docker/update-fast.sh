#!/bin/bash

# Exit on any error
set -e

# Find the script's directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

echo "⚡ Starte FAST Update Prozess (Kein Rebuild)..."

# Move to the project root directory
cd "$ROOT_DIR"

# Pull new changes from git
echo "⏬ Pulling from git repository..."
git pull origin $(git rev-parse --abbrev-ref HEAD)

# Fix permissions
echo "🔐 Setze Dateiberechtigungen..."
chmod -R a+rwX .
chmod +x manage.py

# Ensure data directory exists
echo "📁 Bereite Datenverzeichnis vor..."
mkdir -p "$ROOT_DIR/data"
chmod -R 777 "$ROOT_DIR/data"

# Database migrations
echo "⚙️ Prüfe Datenbank Migrationen (Registry & alle Mandanten)..."
docker compose exec web python manage.py migrate_all

# Collect static files
echo "🎨 Sammle statische Dateien..."
docker compose exec web python manage.py collectstatic --noinput

# Update/Restart the services
echo "🔄 Starte Container neu..."
docker compose up -d
docker compose restart web

echo "-----------------------------------"
echo "✅ FAST Update abgeschlossen!"
