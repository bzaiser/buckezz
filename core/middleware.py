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
                # Mandant existiert nicht -> Schöne Fehlermeldung mit Hilfestellung und Registrierungs-Link
                set_active_tenant(None)
                parts = host.split('.')
                
                # Port ermitteln, um auch in lokaler Entwicklung richtig umzuleiten
                full_host = request.get_host()
                port_suffix = ""
                if ":" in full_host:
                    port_suffix = ":" + full_host.split(":")[1]
                
                # Haupt-Host bestimmen
                if parts[-1] == 'localhost':
                    main_host = f"localhost{port_suffix}"
                else:
                    # Hauptdomain im Live-Betrieb
                    main_host = f"buckezz.zaisers.myds.me{port_suffix}"
                
                register_url = f"{request.scheme}://{main_host}/register/"
                home_url = f"{request.scheme}://{main_host}/"
                
                from django.shortcuts import render
                return render(request, 'core/tenant_not_found.html', {
                    'register_url': register_url,
                    'home_url': home_url,
                    'invalid_slug': tenant_slug
                }, status=404)
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
        if host.endswith('buckezz.zaisers.myds.me'):
            if len(parts) > 4:
                return parts[0]
            return None

        # Allgemeiner Fall
        if len(parts) > 3:
            if parts[0] == 'www':
                return None
            return parts[0]
            
        return None

