from django.core.management.base import BaseCommand
from django.utils import timezone
from django.core.mail import send_mail
from core.models import ListItem

class Command(BaseCommand):
    help = 'Sends email reminders for due items'

    def handle(self, *args, **options):
        now = timezone.now()
        items = ListItem.objects.filter(
            reminder_at__lte=now,
            is_completed=False,
            reminder_sent=False
        )
        
        total = items.count()
        if total == 0:
            self.stdout.write(self.style.SUCCESS(f'Keine fälligen E-Mail-Erinnerungen gefunden (Datum in der Vergangenheit, nicht erledigt, noch nicht gesendet).'))
            return
            
        self.stdout.write(f'{total} fällige Erinnerung(en) gefunden. Starte E-Mail-Versand...')
        
        for item in items:
            subject = f'Erinnerung: {item.title}'
            message = f'Hallo!\n\nDies ist eine Erinnerung für deinen Eintrag "{item.title}" in der Liste "{item.bucket_list.title}".\n\nNotizen: {item.notes}\n\nDein Buckezz Team'
            recipient_list = [item.bucket_list.owner.email]
            
            if recipient_list[0]:
                try:
                    send_mail(subject, message, None, recipient_list)
                    item.reminder_sent = True
                    item.save()
                    self.stdout.write(self.style.SUCCESS(f'Erinnerung für "{item.title}" erfolgreich an {recipient_list[0]} gesendet.'))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'Fehler beim Senden der Erinnerung für "{item.title}": {str(e)}'))
            else:
                self.stdout.write(self.style.WARNING(f'Übersprungen: Der Besitzer der Liste "{item.bucket_list.title}" hat keine E-Mail-Adresse hinterlegt.'))
