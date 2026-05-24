import os
from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.conf import settings
from core.models import Tenant
from core.router import register_tenant_db

class Command(BaseCommand):
    help = 'Führt Migrationen für die Registry-DB und alle isolierten Mandanten-Datenbanken aus.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING("1. Migriere Registry-Datenbank (default)..."))
        call_command('migrate', database='default', interactive=False)

        # Alle registrierten Mandanten ermitteln
        tenants = Tenant.objects.using('default').all()
        self.stdout.write(self.style.SUCCESS(f"Gefunden: {tenants.count()} registrierte(r) Mandant(en)."))

        # Für jeden Mandanten die Migration ausführen
        for tenant in tenants:
            self.stdout.write(self.style.MIGRATE_HEADING(f"\n2. Migriere Mandant '{tenant.name}' ({tenant.slug})..."))
            try:
                db_alias = register_tenant_db(tenant.slug)
                call_command('migrate', database=db_alias, interactive=False)
                call_command('seed_templates', database=db_alias)
                self.stdout.write(self.style.SUCCESS(f"✅ Mandant '{tenant.slug}' erfolgreich migriert und Templates eingespielt."))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"❌ Fehler bei der Migration von '{tenant.slug}': {e}"))

        # Zuletzt die Master-Vorlage neu generieren, damit neue Registrierungen aktuell sind
        self.stdout.write(self.style.MIGRATE_HEADING("\n3. Aktualisiere Master-Vorlage-Datenbank..."))
        try:
            call_command('build_template_db')
            self.stdout.write(self.style.SUCCESS("✅ Master-Vorlage erfolgreich aktualisiert."))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Fehler beim Aktualisieren der Master-Vorlage: {e}"))

        self.stdout.write(self.style.SUCCESS("\n🎉 Alle Datenbank-Migrationen erfolgreich abgeschlossen!"))
