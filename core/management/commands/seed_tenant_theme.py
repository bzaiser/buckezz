from django.core.management.base import BaseCommand
from django.core.management import call_command
from core.router import register_tenant_db
from core.models import Tenant

class Command(BaseCommand):
    help = 'Lädt das standardisierte Admin-Design (Farben, Logo...) in einen bestimmten Mandanten.'

    def add_arguments(self, parser):
        parser.add_argument('tenant_slug', type=str, help='Der Slug/die Subdomain des Mandanten')

    def handle(self, *args, **options):
        tenant_slug = options['tenant_slug']
        self.stdout.write(f"🎨 Starte Theme-Seeding für Mandant: {tenant_slug}")

        try:
            # Prüfen, ob der Mandant existiert
            tenant = Tenant.objects.using('default').filter(slug=tenant_slug).first()
            if not tenant:
                self.stderr.write(self.style.ERROR(f"❌ Mandant '{tenant_slug}' existiert nicht in der Zentral-Datenbank!"))
                return

            # Tenant-Datenbank registrieren
            db_alias = register_tenant_db(tenant_slug)

            # Fixture in diese Datenbank laden
            self.stdout.write(f"🎨 Lade custom_theme.json in Datenbank '{db_alias}'...")
            call_command('loaddata', 'custom_theme.json', database=db_alias, verbosity=1)

            self.stdout.write(self.style.SUCCESS(f"✅ Admin-Design für Mandant '{tenant_slug}' wurde erfolgreich eingespielt!"))

        except Exception as e:
            self.stderr.write(self.style.ERROR(f"❌ Fehler beim Einspielen des Admin-Designs: {e}"))
