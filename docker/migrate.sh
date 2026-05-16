#!/bin/bash
# Buckezz Migration-Script
echo "🔄 Führe Datenbank-Migrationen aus..."
docker-compose run --rm web python manage.py migrate
echo "✅ Fertig."
