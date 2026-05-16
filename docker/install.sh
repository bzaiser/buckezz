#!/bin/bash
# Buckezz Initial Installation Script

echo "🚀 Starte Buckezz Erstinstallation..."

# 1. Check for .env file
if [ ! -f ".env" ]; then
    echo "⚠️  WARNUNG: Keine .env Datei gefunden!"
    echo "Bitte erstelle eine .env Datei mit den nötigen Variablen (SECRET_KEY, ALLOWED_HOSTS, etc.), bevor du fortfährst."
    exit 1
fi

# 2. Prepare Data Directory
echo "📂 Bereite Datenverzeichnis vor..."
mkdir -p data
chmod -R 777 data

# 3. Build and Start Containers
echo "🐳 Baue und starte Docker-Container..."
docker compose up -d --build

# Wait a moment to ensure DB and Web are ready
echo "⏳ Warte auf Container..."
sleep 5

# 4. Run Migrations
echo "🏗️  Erstelle Datenbankstruktur (Migrationen)..."
docker compose exec web python manage.py migrate

# 5. Collect Static Files
echo "🎨 Sammle statische Dateien..."
docker compose exec web python manage.py collectstatic --noinput

# 6. Seed Templates
echo "🌱 Lade Standard-Vorlagen (Buckets) in die Datenbank..."
docker compose exec web python manage.py seed_templates

echo "============================================================"
echo "✅ Installation erfolgreich abgeschlossen!"
echo "Buckezz läuft jetzt unter http://localhost:8006 (oder deiner konfigurierten Domain)."
echo ""
echo "🛑 WICHTIG: Du musst jetzt noch einen Admin-Account anlegen!"
echo "Führe dazu folgenden Befehl aus:"
echo "docker compose exec web python manage.py createsuperuser"
echo "============================================================"
