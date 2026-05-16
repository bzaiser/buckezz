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
        
        for item in items:
            subject = f'Erinnerung: {item.title}'
            message = f'Hallo!\n\nDies ist eine Erinnerung für deinen Eintrag "{item.title}" in der Liste "{item.bucket_list.title}".\n\nNotizen: {item.notes}\n\nDein Buckezz Team'
            recipient_list = [item.bucket_list.owner.email]
            
            if recipient_list[0]:
                try:
                    send_mail(subject, message, None, recipient_list)
                    item.reminder_sent = True
                    item.save()
                    self.stdout.write(self.style.SUCCESS(f'Sent reminder for {item.title} to {recipient_list[0]}'))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'Failed to send reminder for {item.title}: {str(e)}'))
