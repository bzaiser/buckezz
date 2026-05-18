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
