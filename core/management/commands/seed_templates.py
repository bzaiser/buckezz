from django.core.management.base import BaseCommand
from core.models import ListCategory, ListTemplate
from django.db import transaction
from django.utils.text import slugify

class Command(BaseCommand):
    help = 'Seeds sensible list templates and cleans up icons'

    def handle(self, *args, **options):
        templates_data = [
            {
                'old_name': '🛒 Einkaufsliste',
                'name': 'Einkaufsliste',
                'icon': '🛒',
                'fields': {'use_amount': True, 'use_brand': True, 'use_shop': True, 'use_price': True}
            },
            {
                'old_name': '✅ To-Do Liste',
                'name': 'To-Do Liste',
                'icon': '✅',
                'fields': {'use_end_date': True, 'use_persons': True}
            },
            {
                'old_name': '🍷 Weinvorrat',
                'name': 'Weinvorrat',
                'icon': '🍷',
                'fields': {'use_amount': True, 'use_brand': True, 'use_location': True}
            },
             {
                'old_name': '🗓️ Veranstaltungsplaner',
                'name': 'Veranstaltungsplaner',
                'icon': '🗓️',
                'fields': {'use_location': True, 'use_start_date': True, 'use_end_date': True, 'use_persons': True, 'use_price': True}
            },
            {
                'old_name': '💊 Medikamentenplan',
                'name': 'Medikamentenplan',
                'icon': '💊',
                'fields': {'use_amount': True, 'use_start_date': True, 'use_persons': True}
            },
            {
                'old_name': '🎬 Wunschliste',
                'name': 'Wunschliste',
                'icon': '🎬',
                'fields': {'use_location': True, 'use_persons': True}
            }
        ]

        with transaction.atomic():
            for data in templates_data:
                # Try to find by old name or new name
                cat = ListCategory.objects.filter(name__in=[data.get('old_name'), data['name']]).first()
                if not cat:
                    cat = ListCategory.objects.create(name=data['name'], slug=slugify(data['name']))
                
                cat.name = data['name']
                cat.icon = data['icon']
                cat.slug = slugify(data['name'])
                cat.save()
                
                full_fields = {
                    'use_amount': False, 'use_brand': False, 'use_shop': False,
                    'use_price': False, 'use_location': False, 'use_start_date': False,
                    'use_end_date': False, 'use_persons': False, 'use_reminder': False
                }
                full_fields.update(data['fields'])
                
                ListTemplate.objects.update_or_create(
                    category=cat,
                    defaults=full_fields
                )
                self.stdout.write(self.style.SUCCESS(f"Updated {cat.name} with icon {cat.icon}"))
