import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'buckezz.settings')
django.setup()

from core.models import ItemPersonRole
from django.test import Client

c = Client()
role = ItemPersonRole.objects.first()
print('Initial role:', role.role)

response = c.post(f'/role/{role.id}/cycle/', HTTP_HX_REQUEST='true')
print('Response code:', response.status_code)

role.refresh_from_db()
print('Role after cycle 1:', role.role)

response = c.post(f'/role/{role.id}/cycle/', HTTP_HX_REQUEST='true')
role.refresh_from_db()
print('Role after cycle 2:', role.role)
