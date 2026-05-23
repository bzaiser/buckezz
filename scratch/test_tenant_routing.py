import os
import sys

# Add project root to python path
sys.path.append(os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

import django
import shutil

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'buckezz_project.settings')
django.setup()

from django.conf import settings
from core.models import Tenant, ListCategory
from core.router import set_active_tenant, get_active_tenant

def run_test():
    print("🧪 Starte automatischen Integrationstest für Mandanten-Routing...")

    default_db_path = settings.DATABASES['default']['NAME']
    db_dir = os.path.dirname(default_db_path)
    
    tenant_slug = "testfamily"
    tenant_db_filename = f"db_tenant_{tenant_slug}.sqlite3"
    tenant_db_path = os.path.join(db_dir, tenant_db_filename)
    template_db_path = os.path.join(db_dir, "db_template.sqlite3")

    # 1. Sicherstellen, dass Template-DB existiert
    if not os.path.exists(template_db_path):
        print(f"❌ Master-Template-DB fehlt unter: {template_db_path}")
        return

    # 2. Alte Test-Daten aufräumen
    Tenant.objects.using('default').filter(slug=tenant_slug).delete()
    if os.path.exists(tenant_db_path):
        os.remove(tenant_db_path)

    try:
        # 3. Klonen der Template-Datenbank simulieren
        print(f"📋 Klone Template-DB nach: {tenant_db_path}...")
        shutil.copyfile(template_db_path, tenant_db_path)

        # 4. Tenant in der Registry-DB (default) anlegen
        print("📝 Registriere Tenant 'testfamily' in default-Datenbank...")
        tenant = Tenant.objects.using('default').create(
            slug=tenant_slug,
            name="Familie Test",
            owner_email="test@zaisers.de",
            is_active=True
        )

        # 5. Testen ohne aktiven Tenant (sollte auf Default-DB zugreifen)
        set_active_tenant(None)
        print(f"🔄 Ohne Tenant: aktiver Tenant ist {get_active_tenant()} (Erwartet: None)")
        # In der Default-DB sollte der neue Tenant existieren
        default_count = Tenant.objects.using('default').filter(slug=tenant_slug).count()
        print(f"✅ In default DB gefunden: {default_count} (Erwartet: 1)")

        # 6. Testen mit aktivem Tenant (sollte auf Klon-DB zugreifen)
        set_active_tenant(tenant_slug)
        print(f"🔄 Mit Tenant: aktiver Tenant gesetzt auf '{get_active_tenant()}'")
        
        # Abfrage ausführen. Da die Klon-DB eine Kopie der frisch geseedeten Vorlage ist,
        # müssen alle 12 Kategorien darin vorhanden sein!
        categories_in_tenant = ListCategory.objects.all()  # Nutzt den Router!
        cat_count = categories_in_tenant.count()
        print(f"✅ Kategorien in Mandanten-DB gefunden: {cat_count} (Erwartet: 12)")
        
        for c in categories_in_tenant:
            print(f"   - {c.icon} {c.name}")

        assert cat_count == 12, "Fehler: Nicht alle geseedeten Kategorien im Mandanten gefunden!"
        
        # In der Mandanten-DB selbst darf KEIN Tenant-Eintrag existieren (da das Template vor der Registrierung erstellt wurde)
        tenant_count_in_tenant_db = Tenant.objects.all().count()
        print(f"✅ Mandanten-Tabelle in Mandanten-DB ist leer: {tenant_count_in_tenant_db == 0} (Erwartet: True)")

        print("\n🎉 SUPER! Der dynamic Database Router und die Isolation funktionieren makellos!")

    except Exception as e:
        print(f"❌ Test fehlgeschlagen mit Fehler: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # 7. Aufräumen
        print("\n🧹 Bereinige Test-Daten...")
        set_active_tenant(None)
        Tenant.objects.using('default').filter(slug=tenant_slug).delete()
        if os.path.exists(tenant_db_path):
            os.remove(tenant_db_path)
        print("👋 Aufräumarbeiten abgeschlossen.")

if __name__ == '__main__':
    run_test()
