#!/bin/bash
# Buckezz Migration-Script
echo "🔄 Führe Datenbank-Migrationen für Registry & alle Mandanten aus..."
docker-compose run --rm web python manage.py migrate_all
echo "✅ Fertig."
