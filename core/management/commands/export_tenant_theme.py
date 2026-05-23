import os
from django.core.management.base import BaseCommand
from django.conf import settings
from django.db import connections
from django.core import serializers

class Command(BaseCommand):
    help = 'Exportiert das Admin-Design (Theme) eines bestimmten Mandanten als JSON-Fixture'

    def add_arguments(self, parser):
        parser.add_argument('tenant_slug', type=str, help='Der Slug des Mandanten (z.B. schmidt)')

    def handle(self, *args, **options):
        tenant_slug = options['tenant_slug'].lower()
        self.stdout.write(f"🔍 Exportiere Design für Mandant: '{tenant_slug}'...")

        # 1. Pfad der Mandanten-Datenbank ermitteln
        db_name = f"db_tenant_{tenant_slug}.sqlite3"
        db_path = os.path.join(settings.BASE_DIR, db_name)

        if not os.path.exists(db_path):
            self.stderr.write(self.style.ERROR(f"❌ Datenbank-Datei für Mandant '{tenant_slug}' existiert nicht unter: {db_path}"))
            return

        # 2. Temporäre Datenbankverbindung für den Export registrieren
        db_config = {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': db_path,
        }
        settings.DATABASES['temp_export'] = db_config

        try:
            from admin_interface.models import Theme

            # 3. Daten aus der Mandanten-DB auslesen
            themes = Theme.objects.using('temp_export').all()
            if not themes.exists():
                self.stderr.write(self.style.WARNING(f"⚠️ Keine Themes in der Datenbank von '{tenant_slug}' gefunden. Es wird das Standard-Theme exportiert."))
            
            # 4. In Fixture-Format serialisieren
            data = serializers.serialize("json", themes, indent=4)
            
            # 5. Im Fixture-Ordner abspeichern
            fixture_dir = os.path.join(settings.BASE_DIR, 'core', 'fixtures')
            os.makedirs(fixture_dir, exist_ok=True)
            fixture_path = os.path.join(fixture_dir, 'custom_theme.json')
            
            with open(fixture_path, 'w', encoding='utf-8') as f:
                f.write(data)
                
            self.stdout.write(self.style.SUCCESS(f"✅ Design erfolgreich exportiert nach: {fixture_path}"))
            self.stdout.write(self.style.SUCCESS("💡 Du kannst diese Datei nun commiten und pushen."))

        except Exception as e:
            self.stderr.write(self.style.ERROR(f"❌ Fehler beim Exportieren des Designs: {e}"))
        finally:
            # Verbindung sauber schließen und aufräumen
            if 'temp_export' in connections:
                connections['temp_export'].close()
                del connections['temp_export']
            if 'temp_export' in settings.DATABASES:
                del settings.DATABASES['temp_export']
