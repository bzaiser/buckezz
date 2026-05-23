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
        db_alias = 'temp_export'

        if tenant_slug in ['default', 'main', 'master']:
            self.stdout.write("🔍 Exportiere aktives Design aus der Hauptdatenbank (default)...")
            db_config = settings.DATABASES['default'].copy()
            settings.DATABASES[db_alias] = db_config
        else:
            self.stdout.write(f"🔍 Exportiere aktives Design für Mandant: '{tenant_slug}'...")
            db_name = f"db_tenant_{tenant_slug}.sqlite3"
            db_path = os.path.join(settings.BASE_DIR, db_name)

            if not os.path.exists(db_path):
                self.stderr.write(self.style.ERROR(f"❌ Datenbank-Datei für Mandant '{tenant_slug}' existiert nicht unter: {db_path}"))
                return

            db_config = {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': db_path,
            }
            settings.DATABASES[db_alias] = db_config

        try:
            from admin_interface.models import Theme

            # 2. Nur das AKTIVE Theme auslesen
            themes = Theme.objects.using(db_alias).filter(active=True)
            if not themes.exists():
                self.stderr.write(self.style.WARNING(f"⚠️ Kein aktives Theme in '{tenant_slug}' gefunden. Suche nach allen Themes..."))
                themes = Theme.objects.using(db_alias).all()
            
            if not themes.exists():
                self.stderr.write(self.style.ERROR("❌ Keine Themes zum Exportieren gefunden."))
                return

            # 3. In Fixture-Format serialisieren
            data = serializers.serialize("json", themes, indent=4)
            
            # 4. Im Fixture-Ordner abspeichern
            fixture_dir = os.path.join(settings.BASE_DIR, 'core', 'fixtures')
            os.makedirs(fixture_dir, exist_ok=True)
            fixture_path = os.path.join(fixture_dir, 'custom_theme.json')
            
            with open(fixture_path, 'w', encoding='utf-8') as f:
                f.write(data)
                
            self.stdout.write(self.style.SUCCESS(f"✅ Aktives Design erfolgreich exportiert nach: {fixture_path}"))
            self.stdout.write(self.style.SUCCESS("💡 Du kannst diese Datei nun commiten und pushen."))

        except Exception as e:
            self.stderr.write(self.style.ERROR(f"❌ Fehler beim Exportieren des Designs: {e}"))
        finally:
            # Verbindung sauber schließen und aufräumen
            if db_alias in connections:
                connections[db_alias].close()
                del connections[db_alias]
            if db_alias in settings.DATABASES:
                del settings.DATABASES[db_alias]
