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
*   **Smart Templates:** Vorkonfigurierte Buckets (z. B. Einkaufslisten, Reiseplanung, Finanzen) mit integrierten **Hilfe-Modals** und formatierten Praxisbeispielen (Multi-Line Whitespace).
*   **PDF-Export:** Buckets und Listen per Knopfdruck als PDF ausgeben.
*   **Echtzeit-Updates:** Integrierte Alpine.js & HTMX Logik für nahtlose UI-Interaktionen ohne Page-Reloads.

### 🆕 Neu hinzugefügte Premium-Features:

*   **🌍 Reisesicherer Zeitzonen-Auto-Sync (Hybrid-Engine):**
    *   **Im Browser:** Vollautomatische Standorterkennung auf Reisen! Das System liest die lokale Zeitzone deines aktuellen Aufenthaltsortes aus (z. B. auf Reisen in Griechenland) und stellt die gesamte Web-App ohne einen einzigen Klick in Echtzeit auf die Ortszeit um.
    *   **In den Einstellungen:** Möglichkeit zur Festlegung einer permanenten **Heimat-Zeitzone** (z. B. für stabilen Outlook-Sync) in den Design-Einstellungen mit einem komfortablen **🌍 Auto-Erkennungs-Button**.
*   **📅 Outlook- & Google-Kalender-Sync (iCal-Feed):**
    *   Generiert einen RFC 5545-konformen `.ics`-Abonnement-Feed.
    *   Nutzt einen geschützten, persönlichen Sicherheits-Token (`UUIDField`), um Kalender ohne Session-Zwang synchron zu halten.
    *   Premium Glassmorphismus-Panel zum einfachen Kopieren der Feed-URL direkt im Kalender-Reiter.
*   **📧 Smarte E-Mail-Erinnerungen & NAS-Cron-Integration:**
    *   Automatisierter E-Mail-Versand fälliger Listeneinträge an den Listeneigentümer.
    *   **Echtzeit-Status-Badges:** Direkt in den Listen siehst du am Symbol, ob eine Erinnerung noch aussteht (`⏰ [Zeit] Uhr`) oder bereits erfolgreich verschickt wurde (`📩 [Zeit] Uhr (gesendet)`).
    *   Optimiert für Synology NAS Aufgabenplaner mit ausgiebiger Fehlerbehandlung und Protokollierung.
*   **📋 Admin-Kopierfunktion ("Ausgewählte Listen duplizieren"):**
    *   Ermöglicht das schnelle Duplizieren kompletter Listen im Django-Admin mit einem Klick.
    *   Kopiert verknüpfte Teilnehmer (`ListParticipant`), Listeneinträge (`ListItem`) samt Preisen, Shops, Marken und sogar zugewiesenen Personen-Rollen (`ItemPersonRole`), setzt jedoch den Erledigt-Status und die Erinnerungs-Marker für einen frischen Neustart zurück.

---

## 🚀 Installation & Deployment (NAS / Server)

Die App ist für den reibungslosen Betrieb über Docker konzipiert. Die Datenbank (SQLite) wird persistent auf dem Host gespeichert.

### 1. Vorbereitung
Kopiere das Repository auf deinen Server und erstelle im Hauptverzeichnis eine `.env` Datei mit folgendem Inhalt (Werte entsprechend anpassen). Eine ausführliche Vorlage findest du in `.env.example`:

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

# E-Mail (SMTP) Einstellungen für Erinnerungen
EMAIL_HOST=smtp.dein-anbieter.de
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=deine-email@anbieter.de
EMAIL_HOST_PASSWORD=dein-smtp-passwort
DEFAULT_FROM_EMAIL=Buckezz <noreply@deine.domain.de>
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

---

## ⏰ E-Mail-Erinnerungen auf Synology NAS einrichten

Um den regelmäßigen E-Mail-Versand der Erinnerungen auf einer Synology NAS zu automatisieren, nutze den **DSM Aufgabenplaner**:

1. Öffne **Systemsteuerung** > **Aufgabenplaner** auf deiner Synology.
2. Klicke auf **Erstellen** > **Geplante Aufgabe** > **Benutzerdefiniertes Skript**.
3. **Allgemein:**
   * **Aufgabe:** `Buckezz Erinnerungen`
   * **Benutzer:** **`root`** (zwingend erforderlich, um Docker-Befehle auszuführen!)
4. **Zeitplan:**
   * Wähle z. B. **Täglich**, Ausführen alle **15 Minuten** (oder stündlich, je nach Bedarf).
5. **Aufgabeneinstellungen:**
   * Trage bei **Benutzerdefiniertes Skript** Folgenden Befehl ein (anpassen an den Containernamen):
     ```bash
     docker exec buckezz-web-1 python manage.py send_reminders
     ```
   * Aktiviere *"Ergebnisse über E-Mail senden"*, wenn du Fehlermeldungen erhalten möchtest, oder leite den Output in eine Protokolldatei um.

---

## 🛠️ Wartung & Updates

Wenn du neuen Code per Git gezogen hast, kannst du die App ganz einfach über das Update-Skript aktualisieren:

```bash
./docker/update.sh
```

## 📂 Technologie-Stack

*   **Backend:** Python / Django 5.x
*   **Datenbank:** SQLite (via Volume eingebunden)
*   **Frontend:** HTML5, Vanilla CSS (Custom Properties), HTMX, Alpine.js
*   **Kalender:** RFC 5545 iCalendar Feeds / FullCalendar
*   **Server:** WhiteNoise (Statische Dateien), Docker Compose
