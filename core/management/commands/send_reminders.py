from django.core.management.base import BaseCommand
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from core.models import ListItem, Tenant
from core.router import set_active_tenant
from urllib.parse import urlparse
import environ
import os

class Command(BaseCommand):
    help = 'Sends email reminders for due items across all tenant databases'

    def handle(self, *args, **options):
        now = timezone.now()

        # Determine the base URL dynamically
        env = environ.Env()
        base_url = env('BASE_URL', default=None)
        if not base_url:
            trusted_origins = getattr(settings, 'CSRF_TRUSTED_ORIGINS', [])
            external_origins = [o for o in trusted_origins if 'localhost' not in o and '127.0.0.1' not in o]
            if external_origins:
                base_url = external_origins[0]
            else:
                allowed_hosts = getattr(settings, 'ALLOWED_HOSTS', [])
                external_hosts = [h for h in allowed_hosts if h and not h.startswith('.') and 'localhost' not in h and '127.0.0.1' not in h]
                if external_hosts:
                    base_url = f"https://{external_hosts[0]}"
                else:
                    base_url = "http://localhost:8000"
        
        # Strip trailing slash if present
        if base_url.endswith('/'):
            base_url = base_url[:-1]

        # Parse scheme and netloc to construct tenant URLs properly
        parsed_url = urlparse(base_url)
        scheme = parsed_url.scheme or 'https'
        netloc = parsed_url.netloc or 'localhost:8000'

        # Fetch all registered tenants from the registry (default) database
        tenants = Tenant.objects.using('default').all()
        if not tenants.exists():
            self.stdout.write(self.style.WARNING('Keine Mandanten (Tenants) in der Registry-Datenbank gefunden.'))
            return

        self.stdout.write(self.style.SUCCESS(f'Starte E-Mail-Erinnerungen für {tenants.count()} Mandant(en)...'))

        for tenant in tenants:
            self.stdout.write(self.style.NOTICE(f'\n--- Verarbeite Mandant: {tenant.name} ({tenant.slug}) ---'))
            
            # Switch database context to this tenant
            set_active_tenant(tenant.slug)

            # Build the tenant specific base URL
            if 'localhost' in netloc or '127.0.0.1' in netloc:
                tenant_base_url = f"{scheme}://{netloc}"
            elif netloc.startswith('buckezz.'):
                # Replace 'buckezz.' subdomain with tenant subdomain (e.g. 'simon.')
                tenant_base_url = f"{scheme}://{tenant.slug}.{netloc[8:]}"
            else:
                # Prepend tenant subdomain (e.g. 'simon.zaisers.myds.me')
                tenant_base_url = f"{scheme}://{tenant.slug}.{netloc}"

            # Query the active tenant's database for due items
            items = ListItem.objects.filter(
                reminder_at__lte=now,
                is_completed=False,
                reminder_sent=False
            )
            
            total = items.count()
            if total == 0:
                self.stdout.write(self.style.SUCCESS(f'Keine fälligen E-Mail-Erinnerungen für "{tenant.slug}" gefunden.'))
                continue
                
            self.stdout.write(f'{total} fällige Erinnerung(en) gefunden. Starte E-Mail-Versand...')
            
            for item in items:
                subject = f'Erinnerung: {item.title}'
                item_url = f"{tenant_base_url}/list/{item.bucket_list.id}/#item-{item.id}"
                
                message = (
                    f'Hallo!\n\n'
                    f'Dies ist eine Erinnerung für deinen Eintrag "{item.title}" in der Liste "{item.bucket_list.title}".\n\n'
                    f'Direktlink zum Eintrag:\n{item_url}\n\n'
                    f'Notizen:\n{item.notes or "Keine Notizen vorhanden."}\n\n'
                    f'Dein Buckezz Team'
                )
                
                # Collect recipient emails
                recipients = set()
                if item.bucket_list.owner.email:
                    recipients.add(item.bucket_list.owner.email)
                
                for role in item.person_roles.all():
                    if role.person.user and role.person.user.email:
                        recipients.add(role.person.user.email)
                        
                recipient_list = list(recipients)
                
                if recipient_list:
                    try:
                        send_mail(subject, message, None, recipient_list)
                        item.reminder_sent = True
                        item.save()
                        self.stdout.write(self.style.SUCCESS(f'Erinnerung für "{item.title}" erfolgreich an {", ".join(recipient_list)} gesendet.'))
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f'Fehler beim Senden der Erinnerung für "{item.title}": {str(e)}'))
                else:
                    self.stdout.write(self.style.WARNING(f'Übersprungen: Es konnte kein Empfänger (weder Listenbesitzer noch zugewiesene Personen) mit E-Mail-Adresse für "{item.title}" gefunden werden.'))
