from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('pwa.urls')),
    path('', include('core.urls')),
]

handler404 = 'core.views.custom_404_view'

# Media-Dateien immer über Django ausliefern (DEBUG und Produktion mit Gunicorn)
# Whitenoise o.ä. nicht vorhanden – Django übernimmt das direkt
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
