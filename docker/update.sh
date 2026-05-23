#!/bin/bash

# Exit on any error
set -e

# Find the script's directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

echo "🚀 Starte FULL Update Prozess für Buckezz..."

# Move to the project root directory for all operations
cd "$ROOT_DIR"

# Pull new changes from git
echo "⏬ Pulling from git repository..."
git pull origin $(git rev-parse --abbrev-ref HEAD)

# Fix permissions
echo "🔐 Setze Dateiberechtigungen..."
chmod -R a+rwX .
chmod +x manage.py

# Ensure data directory is writeable
echo "📁 Bereite Datenverzeichnis vor..."
mkdir -p "$ROOT_DIR/data"
chmod -R 777 "$ROOT_DIR/data"

# Rebuild the docker image
echo "🏗️ Baue Docker Image..."
docker compose build

# Start the container
echo "🚢 Starte Container..."
docker compose up -d

# Install requirements
echo "📦 Synchronisiere Requirements..."
docker compose exec web pip install -q --no-cache-dir -r requirements.txt

# Database migrations
echo "⚙️ Datenbank Migrationen (Registry & alle Mandanten)..."
docker compose exec web python manage.py migrate_all

# Assets
echo "🎨 Sammle statische Dateien..."
docker compose exec web python manage.py collectstatic --noinput

echo "-----------------------------------"
echo "✅ Update abgeschlossen! Buckezz läuft auf Port 8006."
