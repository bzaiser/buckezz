<div align="center">
  <img src="static/img/logo.svg" alt="Buckezz Logo" width="300"/>
  
  <h3>One Bucket for Everything.</h3>
  <p>Eine moderne, responsive Progressive Web App (PWA) zur smarten Listen- und Bucket-Verwaltung.</p>
</div>

---

## 🌟 Features

*   **Dynamisches Theme-System:** Vollständig anpassbares UI-Design (Primärfarbe, Akzentfarbe, Hintergrund, Glastransparenz) in Echtzeit.
*   **Mobile-First Design:** Auf allen Geräten (Smartphone, Tablet, Desktop) optimiertes Layout mit horizontal scrollbaren Tabellen.
*   **Glassmorphismus UI:** Modernes, tiefenwirksames Interface-Design.
*   **Progressive Web App (PWA):** Kann als native App auf dem Smartphone-Homescreen installiert werden.
*   **Smart Templates:** Vorkonfigurierte Buckets (z. B. Einkaufslisten, Reiseplanung, Finanzen).
*   **PDF-Export:** Buckets und Listen per Knopfdruck als PDF ausgeben.
*   **Echtzeit-Updates:** Integrierte Alpine.js & HTMX Logik für nahtlose UI-Interaktionen ohne Page-Reloads.

## 🚀 Installation & Deployment (NAS / Server)

Die App ist für den reibungslosen Betrieb über Docker konzipiert. Die Datenbank (SQLite) wird persistent auf dem Host gespeichert.

### 1. Vorbereitung
Kopiere das Repository auf deinen Server und erstelle im Hauptverzeichnis eine `.env` Datei mit folgendem Inhalt (Werte entsprechend anpassen):

```env
SECRET_KEY=dein-super-geheimes-django-secret
DEBUG=False
ALLOWED_HOSTS=127.0.0.1,localhost,0.0.0.0,deine.domain.de
CSRF_TRUSTED_ORIGINS=https://deine.domain.de

# Datenbank (wird vom Docker-Volume verwaltet)
DB_PATH=/app/data/db.sqlite3

# Docker Settings
WEB_PORT=8006
CONTAINER_NAME=buckezz_web
IMAGE_NAME=buckezz_image
DB_DIR=./data
```

### 2. Erstinstallation (Automated Setup)
Starte das mitgelieferte Installations-Skript. Es kümmert sich um den Docker-Build, die Datenbankmigration, statische Dateien und das Laden der Standard-Vorlagen:

```bash
chmod +x docker/install.sh
./docker/install.sh
```

### 3. Admin-User anlegen
Um dich nach der Installation einzuloggen, musst du einen Administrator erstellen:
```bash
docker compose exec web python manage.py createsuperuser
```

## 🛠️ Wartung & Updates

Wenn du neuen Code per Git gezogen hast, kannst du die App ganz einfach über das Update-Skript aktualisieren:

```bash
./docker/update.sh
```

## 📂 Technologie-Stack

*   **Backend:** Python / Django 5.x
*   **Datenbank:** SQLite (via Volume eingebunden)
*   **Frontend:** HTML5, Vanilla CSS (Custom Properties), HTMX, Alpine.js
*   **Server:** WhiteNoise (Statische Dateien), Docker Compose
