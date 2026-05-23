import os
import shutil
from django.core.management.base import BaseCommand
from django.conf import settings
from django.db import connections
from django.core.management import call_command

class Command(BaseCommand):
    help = 'Erstellt die Master-Vorlage-Datenbank (db_template.sqlite3) frisch aus den Migrationen und Seeds'

    def handle(self, *args, **options):
        self.stdout.write("🏗️ Starte Erstellung der Master-Vorlage-Datenbank...")

        # 1. Pfade bestimmen
        default_db_path = settings.DATABASES['default']['NAME']
        db_dir = os.path.dirname(default_db_path)
        template_db_path = os.path.join(db_dir, 'db_template.sqlite3')

        # 2. Alte Template-DB löschen, falls vorhanden
        if os.path.exists(template_db_path):
            self.stdout.write(f"🗑️ Lösche alte Vorlage unter {template_db_path}...")
            try:
                os.remove(template_db_path)
            except Exception as e:
                self.stderr.write(self.style.ERROR(f"Fehler beim Löschen der alten Vorlage: {e}"))
                return

        # 3. Backup der originalen default DB-Konfiguration
        original_default = settings.DATABASES['default'].copy()

        try:
            # 4. Temporär die default DB auf die neue Template-DB umbiegen
            new_db_config = original_default.copy()
            new_db_config['NAME'] = template_db_path
            settings.DATABASES['default'] = new_db_config

            # Bestehende Verbindung schließen und aus dem Cache löschen
            connections['default'].close()
            del connections['default']

            # 5. Migrationen und Seeds ausführen
            self.stdout.write("🏗️ Führe Django-Datenbank-Migrationen auf der Vorlage aus...")
            call_command('migrate', interactive=False, verbosity=1)

            self.stdout.write("👥 Richte Standard-Gruppen und Berechtigungen ein...")
            call_command('setup_groups')

            self.stdout.write("🌱 Seed-Standardvorlagen (Einkaufsliste, Sport, Gesundheit...) einspielen...")
            call_command('seed_templates')

            self.stdout.write(self.style.SUCCESS(f"✅ Master-Vorlage-Datenbank erfolgreich erstellt unter: {template_db_path}"))

        except Exception as e:
            self.stderr.write(self.style.ERROR(f"❌ Fehler bei der Erstellung der Template-Datenbank: {e}"))
            # Falls die Datei halbfertig ist, aufräumen
            if os.path.exists(template_db_path):
                try:
                    os.remove(template_db_path)
                except:
                    pass
        finally:
            # 6. Originale DB-Verbindung wiederherstellen
            settings.DATABASES['default'] = original_default
            connections['default'].close()
            if 'default' in connections:
                del connections['default']
            self.stdout.write("🔄 Originale DB-Verbindung wiederhergestellt.")
