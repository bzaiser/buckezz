from core.models import ListCategory, ListTemplate
from django.db import transaction

templates_data = [
    {
        'name': '🛒 Einkaufsliste',
        'fields': {
            'use_amount': True,
            'use_brand': True,
            'use_shop': True,
            'use_price': True,
            'use_location': False,
            'use_start_date': False,
            'use_end_date': False,
            'use_persons': False,
        }
    },
    {
        'name': '✅ To-Do Liste',
        'fields': {
            'use_amount': False,
            'use_brand': False,
            'use_shop': False,
            'use_price': False,
            'use_location': False,
            'use_start_date': False,
            'use_end_date': True,
            'use_persons': True,
        }
    },
    {
        'name': '🍷 Bestandsliste (Wein/Vorrat)',
        'fields': {
            'use_amount': True,
            'use_brand': True,
            'use_shop': False,
            'use_price': False,
            'use_location': True,
            'use_start_date': False,
            'use_end_date': False,
            'use_persons': False,
        }
    },
    {
        'name': '🗓️ Veranstaltungsplaner',
        'fields': {
            'use_amount': False,
            'use_brand': False,
            'use_shop': False,
            'use_price': True,
            'use_location': True,
            'use_start_date': True,
            'use_end_date': True,
            'use_persons': True,
        }
    },
    {
        'name': '💊 Medikamentenplan',
        'fields': {
            'use_amount': True,
            'use_brand': False,
            'use_shop': False,
            'use_price': False,
            'use_location': False,
            'use_start_date': True,
            'use_end_date': False,
            'use_persons': True,
        }
    },
    {
        'name': '🎬 Film/Serien-Wunschliste',
        'fields': {
            'use_amount': False,
            'use_brand': False,
            'use_shop': False,
            'use_price': False,
            'use_location': True,
            'use_start_date': False,
            'use_end_date': False,
            'use_persons': True,
            'use_rating': False,
        }
    },
    {
        'name': '🏆 Winliste',
        'fields': {
            'use_amount': False,
            'use_brand': False,
            'use_shop': False,
            'use_price': False,
            'use_location': False,
            'use_start_date': False,
            'use_end_date': False,
            'use_persons': True,
            'use_rating': True,
        }
    }
]

def create_templates():
    with transaction.atomic():
        for data in templates_data:
            template, created = ListTemplate.objects.update_or_create(
                # Use a unique identifier if possible, but here we just match by field set or create new
                **data['fields']
            )
            cat, created = ListCategory.objects.update_or_create(
                name=data['name'],
                defaults={'template': template}
            )
            print(f"{'Created' if created else 'Updated'} category: {cat.name}")

if __name__ == '__main__':
    create_templates()
