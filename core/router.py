import os
import contextvars
from django.conf import settings
from django.db import connections

# Thread/Coroutine-sichere Aufbewahrung des aktiven Mandanten (Subdomain)
_active_tenant = contextvars.ContextVar('active_tenant', default=None)

def get_active_tenant():
    return _active_tenant.get()

def set_active_tenant(tenant_slug):
    _active_tenant.set(tenant_slug)

def register_tenant_db(tenant_slug):
    """
    Registriert eine dynamische SQLite-Verbindung im Django ConnectionHandler,
    falls diese noch nicht geladen wurde.
    """
    db_alias = f"tenant_{tenant_slug}"
    if db_alias not in connections.databases:
        # Pfad der originalen default-DB holen (z. B. /app/db.sqlite3 oder BASE_DIR / db.sqlite3)
        default_db_path = settings.DATABASES['default']['NAME']
        db_dir = os.path.dirname(default_db_path)
        
        # Pfad für die Mandanten-Datenbank zusammensetzen
        tenant_db_path = os.path.join(db_dir, f"db_tenant_{tenant_slug}.sqlite3")
        
        # Einstellungen der default-DB kopieren und Pfad anpassen
        db_config = settings.DATABASES['default'].copy()
        db_config['NAME'] = tenant_db_path
        
        connections.databases[db_alias] = db_config
        
    return db_alias

class TenantRouter:
    """
    Ein Django Datenbank-Router, der alle Queries basierend auf dem aktiven 
    Thread-spezifischen Mandanten auf die korrekte SQLite-Datei umleitet.
    """
    def db_for_read(self, model, **hints):
        active_tenant = get_active_tenant()
        if active_tenant:
            return register_tenant_db(active_tenant)
        return 'default'

    def db_for_write(self, model, **hints):
        active_tenant = get_active_tenant()
        if active_tenant:
            return register_tenant_db(active_tenant)
        return 'default'

    def allow_relation(self, obj1, obj2, **hints):
        # Relationen nur erlauben, wenn sie in der gleichen Datenbank liegen
        db1 = getattr(obj1, '_state', None) and obj1._state.db
        db2 = getattr(obj2, '_state', None) and obj2._state.db
        if db1 and db2:
            return db1 == db2
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        # Migrationen sind auf allen DBs (Registry standard & Tenants) erlaubt.
        # So können wir bei Updates einfach über alle SQLite-Dateien migrieren.
        return True
