import zoneinfo
from django.utils import timezone

class TimezoneMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # 1. Zuerst das Cookie 'django_timezone' prüfen (für vollautomatische Erkennung auf Reisen)
        tzname = request.COOKIES.get('django_timezone')
        
        # 2. Wenn kein Cookie da ist, die in der DB gespeicherte Zeitzone des Users nutzen
        if not tzname and request.user.is_authenticated:
            try:
                tzname = request.user.settings.timezone
            except Exception:
                pass
                
        # 3. Die ermittelte Zeitzone für diesen Request aktivieren
        if tzname:
            try:
                timezone.activate(zoneinfo.ZoneInfo(tzname))
            except Exception:
                timezone.deactivate()
        else:
            timezone.deactivate()
            
        return self.get_response(request)


from django.http import HttpResponseNotFound, HttpResponseRedirect
from core.router import set_active_tenant
from core.models import Tenant

class TenantMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        host = request.get_host().split(':')[0].lower()
        
        # 1. Subdomain ermitteln
        tenant_slug = self.get_subdomain(host)
        
        if tenant_slug:
            # 2. Prüfen, ob der Mandant in der Registry-DB existiert
            tenant = Tenant.objects.using('default').filter(slug=tenant_slug, is_active=True).first()
            if tenant:
                # Mandant aktivieren für diesen Thread/Request
                set_active_tenant(tenant_slug)
                request.tenant = tenant
            else:
                # Mandant existiert nicht -> Umleitung zur Hauptseite
                set_active_tenant(None)
                parts = host.split('.')
                if len(parts) > 3:
                    main_host = '.'.join(parts[1:])
                    return HttpResponseRedirect(f"{request.scheme}://{main_host}/")
                return HttpResponseNotFound("<h3>Dieser Mandant existiert nicht oder ist inaktiv.</h3>")
        else:
            # Hauptseite (Standard-DB)
            set_active_tenant(None)
            request.tenant = None

        response = self.get_response(request)
        
        # Sicherstellen, dass nach dem Request wieder auf Standard zurückgesetzt wird
        set_active_tenant(None)
        
        return response

    def get_subdomain(self, host):
        if host.replace('.', '').isdigit():
            return None
            
        parts = host.split('.')
        
        # Lokale Entwicklung auf localhost
        if parts[-1] == 'localhost':
            if len(parts) > 1:
                return parts[0]
            return None

        # Wildcard-Erkennung für buckezz.zaisers.myds.me
        if host.endswith('buckezz.zaisers.myds.me') and len(parts) > 4:
            return parts[0]

        # Allgemeiner Fall
        if len(parts) > 3:
            if parts[0] == 'www':
                return None
            return parts[0]
            
        return None

