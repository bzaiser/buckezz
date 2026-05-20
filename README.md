<div align="center">
  <img src="static/img/logo.svg" alt="Buckezz Logo" width="300"/>
  
  <h3>One Bucket for Everything.</h3>
  <p>Eine moderne, responsive Progressive Web App (PWA) zur smarten Listen-, To-Do- und Bucket-Verwaltung mit intelligenter Alexa-Sprachsteuerung und reisesicherer Kalendersynchronisation.</p>
</div>

---

## 🌟 Premium Features

*   **Vollständig anpassbares Glassmorphism-UI:** Echtzeit-Theme-System zur Personalisierung von Primärfarbe, Akzentfarbe, Glastransparenz, Hintergrund und Kontrasten.
*   **Mobile-First & PWA:** Optimal abgestimmt auf alle Bildschirmgrößen mit horizontal scrollbaren Listen. Kann direkt über den Webbrowser als native App auf dem Homescreen installiert werden.
*   **Smarte Listen-Vorlagen (Smart Templates):** Vordefinierte Vorlagen wie To-Do-Listen, Weinvorräte, Medikamentenpläne, Haustier-Planer, Pflanzenpflege, Wunschlisten und **🏥 Arzt-Termine**. Jede Liste besitzt interaktive Hilfe-Modals und formatierte Praxisbeispiele.
*   **📧 Intelligente E-Mail-Erinnerungen:**
    *   Sende automatisierte E-Mails bei fälligen To-Dos an alle zugewiesenen Personen.
    *   **Echtzeit-Status-Badges:** Direkt in der Listenansicht siehst du, ob ein Wecker aussteht (`⏰ [Zeit] Uhr`) oder bereits erfolgreich verschickt wurde (`📩 [Zeit] Uhr (gesendet)`).
*   **🌍 Reisesicherer Zeitzonen-Sync & Outlook-Fix (Hybrid-Engine):**
    *   **Im Browser:** Vollautomatische Standorterkennung auf Reisen! Das System liest deine lokale Browser-Zeitzone aus und stellt das Web-Interface in Echtzeit um.
    *   **Im Kalender (Outlook, Google Calendar, Apple):** Exporte und iCal-Abonnements (`.ics`) werden unter Verwendung deiner einstellbaren **Heimat-Zeitzone** und dem standardkonformen `TZID`-Parameter generiert. Dies **verhindert zuverlässig den legendären Microsoft-Outlook-Bug**, der abonnierte UTC-Zeiten bei Sommer-/Winterzeit-Wechseln um 1 bis 2 Stunden verschiebt!
*   **🎙️ Smart Alexa Integration:** Sprich mit deinen Listen! Durch unseren integrierten **deutschen NLP-Parser (Natural Language Processing)** kannst du per Sprache komplexe Einkäufe diktieren, die automatisch in Bezeichnung, menge, Marke, Geschäft und Preis zerlegt werden.

---

## 🛠️ Technologie-Stack

*   **Backend:** Python 3.11 / Django 5.x
*   **Datenbank:** SQLite 3 (persistent über Docker-Volume angebunden)
*   **Frontend:** HTML5, Vanilla CSS (CSS Variables), HTMX (für flüssige Teil-Seiten-Updates), Alpine.js (für reaktive UI-Elemente)
*   **Kalender:** RFC 5545 iCalendar Feeds / FullCalendar
*   **Server / Deployment:** Gunicorn / WhiteNoise (Statische Dateien), Docker Compose

---

## 🚀 Installation & Deployment (Server / NAS)

Die App ist für den reibungslosen Betrieb über Docker Compose konzipiert.

### 1. Die Konfigurationsdatei `.env` erstellen
Erstelle im Hauptverzeichnis deines Servers/NAS eine Datei namens `.env` und befülle sie mit deinen Konfigurationsdaten. Hier ist eine ausführliche Übersicht aller verfügbaren Variablen:

```env
# --- Django Basis-Einstellungen ---
SECRET_KEY=dein-super-geheimes-django-secret-key  # Einzigartiger, geheimer Schlüssel zur Absicherung der Sessions
DEBUG=False                                      # Im Produktivbetrieb IMMER False für optimale Performance & Sicherheit
ALLOWED_HOSTS=localhost,127.0.0.1,deine-domain.de # Komma-separierte Liste von Hostnames/IPs, unter denen die App erreichbar ist
CSRF_TRUSTED_ORIGINS=https://deine-domain.de      # Erforderlich für Formular-Absendungen über HTTPS-Domains

# --- Datenbank-Pfad ---
DB_PATH=/app/data/db.sqlite3                      # Der Pfad zur SQLite-Datenbank innerhalb des Docker-Containers

# --- E-Mail (SMTP) Einstellungen für Erinnerungen ---
EMAIL_HOST=smtp.dein-anbieter.de                 # Dein SMTP-Mailserver (z. B. smtp.strato.de, mail.gmx.net)
EMAIL_PORT=587                                   # Port deines SMTP-Servers (üblicherweise 587 bei TLS, 465 bei SSL)
EMAIL_USE_TLS=True                               # Nutze TLS-Verschlüsselung (empfohlen bei Port 587)
EMAIL_HOST_USER=deine-email@anbieter.de          # Benutzername für deinen E-Mail-Account
EMAIL_HOST_PASSWORD=dein-smtp-passwort           # Passwort (oder App-Passwort) deines E-Mail-Accounts
DEFAULT_FROM_EMAIL=Buckezz <noreply@deine-domain.de> # Der Absendername der Erinnerungs-Mails

# --- Docker Compose Variablen ---
WEB_PORT=8006                                    # Der Port auf dem Host-System, unter dem Buckezz erreichbar sein soll
CONTAINER_NAME=buckezz_web                       # Name des laufenden Docker-Containers
IMAGE_NAME=buckezz_image                         # Name des gebauten Docker-Images
DB_DIR=./data                                    # Lokales Verzeichnis auf dem Host zur Speicherung der Datenbank
```

### 2. Erstinstallation (Automated Setup)
Führe das mitgelieferte Installationsskript aus. Es kümmert sich um den Docker-Build, Datenbank-Migrationen, das Einsammeln statischer Dateien und das Einrichten der Standard-Listen-Vorlagen:

```bash
chmod +x docker/install.sh
./docker/install.sh
```

### 3. Administrator-Konto erstellen
Um dich im System und im Django-Admin-Bereich einloggen zu können, erstelle ein Superuser-Konto:

```bash
docker compose exec web python manage.py createsuperuser
```

---

## ⏰ E-Mail-Erinnerungen auf Synology NAS automatisieren

Um den regelmäßigen Versand der E-Mail-Erinnerungen sicherzustellen, richten wir auf der Synology NAS einen automatisierten Cronjob über den **DSM Aufgabenplaner** ein:

1. Öffne die **Systemsteuerung** auf deiner Synology NAS und navigiere zu **Aufgabenplaner**.
2. Klicke auf **Erstellen** > **Geplante Aufgabe** > **Benutzerdefiniertes Skript**.
3. **Reiter "Allgemein":**
   * **Aufgabe:** `Buckezz E-Mail Erinnerungen`
   * **Benutzer:** **`root`** (Dies ist zwingend notwendig, da der Cronjob die Berechtigung benötigt, Docker-Befehle auf dem System auszuführen!)
   * Aktiviere das Häkchen bei *Aktiviert*.
4. **Reiter "Zeitplan":**
   * **Ausführen an folgenden Tagen:** Täglich
   * **Frequenz:** Ausführen alle **15 Minuten** (oder kürzer/länger, je nach gewünschter Präzision deiner Erinnerungen).
5. **Reiter "Aufgabeneinstellungen":**
   * Gib unter **Benutzerdefiniertes Skript** exakt folgenden Befehl ein:
     ```bash
     docker exec buckezz_web python manage.py send_reminders
     ```
   * *Tipp:* Aktiviere *"Ergebnisse über E-Mail senden"* und trage deine E-Mail-Adresse ein, um im Fehlerfall sofort benachrichtigt zu werden.

---

## 🌍 Zeitzonen & iCal Outlook-Synchronisation (Deep-Dive)

To-Dos und Erinnerungen hängen stark von der Zeitzonen-Genauigkeit ab. Buckezz verwendet ein ausgeklügeltes Zeitzonen-Handling, um Fehler im In- und Ausland komplett auszuschließen.

### Wie das Zeitzonen-Handling funktioniert:

1. **Automatische Browser-Erkennung (Urlaubsmodus):**
   Sobald du die Web-App aufrufst, liest ein JavaScript deine lokale Zeitzone des Browsers aus und speichert sie im Cookie `django_timezone` (z. B. `Europe/Athens`, wenn du in Griechenland bist). Alle Termine, die du auf der Webseite siehst oder einträgst, werden vollautomatisch und **ohne Umrechnung** in dieser Zeitzone angezeigt und verarbeitet.
2. **Heimat-Zeitzone (In den Einstellungen):**
   In deinen **⚙️ Einstellungen** legst du eine feste **Heimat-Zeitzone** fest (z. B. `Europe/Berlin`). Wenn du im Urlaub bist, kannst du auf das schicke **Standort-Pin-Symbol (📍)** klicken, um deine aktuelle Urlaubs-Zeitzone automatisch zu ermitteln, auszuwählen und abzuspeichern.
3. **Der iCal Outlook-Verschiebungs-Fix:**
   Frühere Versionen gaben Kalenderzeiten in Weltzeit (UTC, z. B. `15:00:00Z`) aus. **Microsoft Outlook hat hierbei einen bekannten Fehler:** Bei abonnierten Feeds unterschlägt Outlook oft den Sommer-/Winterzeit-Wechsel (DST) und verschiebt deine Termine um 1 bis 2 Stunden.
   **Die Buckezz-Lösung:** Alle Termine im iCal-Export werden jetzt in deiner lokalen Heimat-Uhrzeit, kombiniert mit dem expliziten Zeitzonen-Parameter (`TZID`), exportiert:
   ```ical
   DTSTART;TZID=Europe/Berlin:20260520T170000
   ```
   Outlook übernimmt diese Zeit dadurch **zu 100 % exakt und unberührt**, wodurch keinerlei Verschiebungen mehr entstehen!

---

## 🎙️ Smart Alexa Integration (Schritt-für-Schritt)

Du kannst Buckezz ganz einfach an deinen **Amazon Alexa Account** anbinden, um Einträge (z. B. auf deine Einkaufsliste) direkt per Sprache zu diktieren. 

Unser integrierter deutscher NLP-Parser versteht komplexe Sätze wie:
> *"Alexa, sag Buckezz setze drei Packungen laktosefreie Milch von Rewe für ein Euro neunundneunzig auf die Liste."*
> **Ergebnis in Buckezz:** Bezeichnung: `laktosefreie Milch` | Menge: `3 Packungen` | Marke: `Rewe` | Preis: `1.99 €`.

### Schritt 1: Deinen persönlichen API-Endpoint finden
Jede deiner Listen in Buckezz hat eine eindeutige ID. Deine persönliche API-Schnittstelle lautet:
`https://deine.domain.de/api/alexa/<listen-uuid-token>/`
*Den genauen Link findest du direkt im Reiter **Teilen / API** deiner jeweiligen Liste in Buckezz.*

### Schritt 2: Custom Skill in der Amazon Developer Console anlegen
1. Melde dich auf der [Amazon Developer Console](https://developer.amazon.com/) an.
2. Klicke auf **Create Skill** (Skill erstellen).
3. **Skill Name:** `Buckezz` (oder ein beliebiger Name deiner Wahl).
4. **Primary Language:** `German` (Deutsch).
5. **Choose a model to add to your skill:** `Custom` (Benutzerdefiniert).
6. **Choose a method to host your skill's backend resources:** `Provision your own` (Eigenes Backend bereitstellen).
7. Klicke oben rechts auf **Create Skill**.

### Schritt 3: Den Endpunkt (Endpoint) hinterlegen
1. Klicke im linken Menü des Skills auf **Endpoint**.
2. Wähle **HTTPS** als Service Endpoint Type aus.
3. Trage im Feld **Default Region** deine persönliche Schnittstellen-URL ein (z. B. `https://deine.domain.de/api/alexa/ad6d142e-8c03-4c68-8c18-b1d9c380c93a/`).
4. Wähle im Dropdown-Menü darunter den SSL-Zertifikatstyp aus: 
   * *„My development endpoint is a sub-domain of a domain that has a wildcard certificate from a certificate authority“* (für Standard-SSL-Zertifikate wie Let's Encrypt).
5. Klicke oben auf **Save Endpoints**.

### Schritt 4: Das Interaktionsmodell (Interaction Model) einspielen
1. Klicke im linken Menü auf **Interaction Model** > **JSON Editor**.
2. Lösche den gesamten Inhalt des Textfeldes und füge das folgende vollständige JSON-Schema ein:

```json
{
  "interactionModel": {
    "languageModel": {
      "invocationName": "buckezz",
      "intents": [
        {
          "name": "AddItemIntent",
          "slots": [
            {
              "name": "item",
              "type": "AMAZON.SearchQuery"
            }
          ],
          "samples": [
            "setze {item} auf die einkaufsliste",
            "packe {item} auf die einkaufsliste",
            "schreibe {item} auf die einkaufsliste",
            "setze {item} auf die liste",
            "packe {item} auf die liste",
            "schreibe {item} auf die liste",
            "füge {item} hinzu",
            "setze {item}",
            "packe {item}"
          ]
        },
        {
          "name": "AMAZON.CancelIntent",
          "samples": []
        },
        {
          "name": "AMAZON.HelpIntent",
          "samples": []
        },
        {
          "name": "AMAZON.StopIntent",
          "samples": []
        },
        {
          "name": "AMAZON.NavigateHomeIntent",
          "samples": []
        },
        {
          "name": "AMAZON.FallbackIntent",
          "samples": []
        }
      ],
      "types": []
    }
  }
}
```

3. Klicke oben auf **Save Model** (Modell speichern).
4. Klicke auf **Build Model** (Modell erstellen). Nach ca. 1-2 Minuten ist das Interaktionsmodell fertig generiert.

### Schritt 5: Testen!
Du kannst den Skill jetzt direkt in der Konsole im Reiter **Test** (oben) oder auf all deinen verknüpften Alexa-Geräten zu Hause aktivieren und testen!
*   *„Alexa, öffne Buckezz!“* -> Antwort: *„Hallo! Welches Element möchtest du auf die Einkaufsliste setzen?“*
*   *„Alexa, sag Buckezz setze Mehl auf die Liste!“* -> Antwort: *„Ich habe Mehl auf deine Liste Einkaufsliste gesetzt.“*
*   *„Alexa, sag Buckezz setze 4 Flaschen trockenen Rotwein von Aldi für 3,99 Euro auf die Liste!“* -> Antwort: *„Ich habe 4 Flaschen trockenen Rotwein von Aldi für 3,99 Euro auf deine Liste Weinvorrat gesetzt.“*

---

## 🔄 Wartung, Updates & PWA-Cache

### App aktualisieren
Wenn ein neues Update bereitsteht, kannst du die Anwendung auf deinem Server/NAS ganz einfach aktualisieren:

```bash
git pull
./docker/update.sh
```

### PWA-Cache auf dem Handy/Browser leeren
Da Progressive Web Apps (PWA) Assets extrem hartnäckig cachen, siehst du Updates auf deinem Handy oft erst verzögert.
* Geh dazu einfach in Buckezz in deine **⚙️ Einstellungen**.
* Scrolle ganz nach unten zum Bereich **📱 App-Cache & PWA**.
* Klicke auf **"🔄 App-Cache leeren & aktualisieren"**. 
* Deine App deregistriert sofort alle Service Worker, löscht den Cache und lädt sich in unter einer Sekunde brandneu vom Server herunter.
