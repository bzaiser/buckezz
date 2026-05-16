#!/bin/bash
# Buckezz Start-Script
echo "🚀 Starte Buckezz auf Port 8006..."
mkdir -p data
chmod -R 777 data
docker compose up -d --build
echo "✅ Buckezz läuft! Erreichbar unter http://localhost:8006 (oder NAS-IP:8006)"
