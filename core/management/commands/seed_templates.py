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
                'fields': {'use_amount': True, 'use_brand': True, 'use_shop': True, 'use_price': True},
                'help_purpose': 'Perfekt für deinen Wocheneinkauf, Vorratsbestellungen oder Besorgungen.',
                'help_fields': 'Wenn du diese Liste wählst, stehen dir folgende nützliche Felder zur Verfügung:\n• Menge: Menge oder Packungsanzahl (z.B. "3" oder "1 Packung")\n• Marke: Produkt-Marke zur genauen Orientierung\n• Geschäft: Wo du den Artikel kaufen möchtest (z.B. "Rewe", "Aldi")\n• Preis: Einzelpreis des Artikels zur automatischen Berechnung der Summe',
                'help_example': 'Bezeichnung: "Hafermilch" | Menge: "4 Packungen" | Marke: "Oatly" | Geschäft: "Edeka" | Preis: "1.99 €"'
            },
            {
                'old_name': '✅ To-Do Liste',
                'name': 'To-Do Liste',
                'icon': '✅',
                'fields': {'use_end_date': True, 'use_persons': True, 'use_reminder': True},
                'help_purpose': 'Strukturierte Erfassung all deiner privaten und beruflichen Aufgaben.',
                'help_fields': 'Nutze folgende Felder zur Aufgabenverwaltung:\n• Fälligkeitsdatum: Bis wann die Aufgabe erledigt sein muss\n• Erinnerung: Stelle Benachrichtigungen ein, um Fristen nicht zu verschlafen\n• Personen: Weise Aufgaben deinen Freunden oder Familienmitgliedern zu!',
                'help_example': 'Bezeichnung: "Wohnzimmer streichen" | Fälligkeit: "Sonntag" | Beteiligt: "Jonas, Papa"'
            },
            {
                'old_name': '🍷 Weinvorrat',
                'name': 'Weinvorrat',
                'icon': '🍷',
                'fields': {'use_amount': True, 'use_brand': True, 'use_location': True},
                'help_purpose': 'Perfekt, um die Übersicht über deinen Weinkeller, Gin-Regale oder deine Hausbar zu behalten.',
                'help_fields': 'Verwalte deine Bestände mit diesen Feldern:\n• Menge: Aktuelle Anzahl an Flaschen (kann in der Liste direkt editiert werden!)\n• Winzer/Marke: Name des Herstellers oder Weinguts\n• Lagerort: Wo genau die Flasche liegt (z.B. "Kellerregal 3, Fach B")',
                'help_example': 'Bezeichnung: "Cabernet Sauvignon 2019" | Menge: "4 Flaschen" | Winzer: "Château Margaux" | Ort: "Fach 5A"'
            },
            {
                'old_name': '🗓️ Veranstaltungsplaner',
                'name': 'Veranstaltungsplaner',
                'icon': '🗓️',
                'fields': {'use_location': True, 'use_start_date': True, 'use_end_date': True, 'use_persons': True, 'use_price': True},
                'help_purpose': 'Perfekt für Geburtstage, Ausflüge, Grillfeste oder Business-Events.',
                'help_fields': 'Koordiniere deine Feiern mit diesen Feldern:\n• Ort: Wo die Feier stattfindet\n• Start & Ende: Genaue Veranstaltungszeiträume\n• Beteiligte Personen: Ordne Aufgaben oder Rollen (z.B. "Salat mitbringen") bestimmten Personen zu\n• Kosten/Budget: Kalkulierte Preise pro Planungs-Posten',
                'help_example': 'Bezeichnung: "Getränke holen" | Ort: "Getränkemarkt Müller" | Start: "18.06.2026 15:00" | Zuständig: "Felix" | Preis: "60.00 €"'
            },
            {
                'old_name': '💊 Medikamentenplan',
                'name': 'Medikamentenplan',
                'icon': '💊',
                'fields': {'use_amount': True, 'use_start_date': True, 'use_persons': True, 'use_tracker': True, 'use_reminder': True},
                'help_purpose': 'Verlässliche Erinnerung und Dokumentation deiner täglichen Medikamente.',
                'help_fields': 'Behalte deine Gesundheit im Griff:\n• Dosierung/Menge: z.B. "1 Tablette" oder "15 Tropfen"\n• Startdatum: Wann die Einnahme-Phase beginnt\n• Erinnerung: Stelle tägliche oder wöchentliche Wecker ein\n• Einnahme-Tracker: Protokolliere Einnahmen in Echtzeit mit einem Klick im Live-Tracker!',
                'help_example': 'Bezeichnung: "Magnesium 400" | Dosis: "1 Kapsel" | Uhrzeit: "20:00 Uhr". Nach dem Schlucken klickst du einfach auf "Eingenommen" zum Protokollieren.'
            },
            {
                'old_name': '🎬 Wunschliste',
                'name': 'Wunschliste',
                'icon': '🎬',
                'fields': {'use_location': True, 'use_persons': True},
                'help_purpose': 'Geschenkideen für Geburtstage, Weihnachten oder Hochzeiten sammeln und verteilen.',
                'help_fields': 'Halte Geschenkideen fest:\n• Geschäft/Link: Wo man den Wunsch kaufen kann (Ort)\n• Wünschende Person: Für wen das Geschenk gedacht ist',
                'help_example': 'Bezeichnung: "Acoustic Guitar" | Shop: "Thomann.de" | Wunsch von: "Sarah"'
            },
            {
                'old_name': '🏆 Winliste',
                'name': 'Winliste',
                'icon': '🏆',
                'fields': {'use_rating': True, 'use_persons': True},
                'help_purpose': 'Positive Erlebnisse, bestandene Prüfungen oder sportliche Meilensteine als Motivation sammeln.',
                'help_fields': 'Dokumentiere deine Siege:\n• Bedeutung (Bewertung): Bewerte das Erlebnis von 1-5 Sternen\n• Geteilt mit: Wer war an diesem glücklichen Tag dabei?',
                'help_example': 'Bezeichnung: "Bachelorarbeit bestanden (1.3)" | Bedeutung: "⭐⭐⭐⭐⭐" | Dabei: "Familie, Freunde"'
            },
            {
                'old_name': '🎯 Bucket List',
                'name': 'Bucket List',
                'icon': '🎯',
                'fields': {'use_milestone': True, 'use_url': True, 'use_rating': True},
                'help_purpose': 'Träume, Abenteuer und Lebensziele planen und festhalten.',
                'help_fields': 'Plane deine Lebensziele:\n• Lebensabschnitt (Milestone): Wann willst du es erreichen? (z.B. "vor 30", "vor 60")\n• Wichtigkeit: Bewertung der Bedeutung von 1-5 Sternen\n• Inspirations-Link: URL mit Reiseinfos oder Bildern\n• Erreicht am: Das Erreicht-am-Datum ist nach dem Abhaken jederzeit nachträglich editierbar, um alte Abenteuer nachzupflegen!',
                'help_example': 'Bezeichnung: "Fallschirmsprung machen" | Milestone: "vor 40" | Wichtigkeit: "⭐⭐⭐⭐⭐" | Link: "skydiving-school.de"'
            },
            {
                'old_name': '🐾 Haustier-Planer',
                'name': 'Haustier-Planer',
                'icon': '🐾',
                'fields': {'use_persons': True, 'use_tracker': True, 'use_reminder': True},
                'help_purpose': 'Perfekt, um die Versorgung von Hund, Katze, Vögeln oder Pferd im Haushalt abzustimmen.',
                'help_fields': 'Organisiere die Tierpflege:\n• Zuständigkeit: Wer füttert das Tier oder geht Gassi?\n• Erinnerung: Tägliche oder wöchentliche Wecker für Medizin, Bürsten, etc.\n• Pflege-Tracker: Logge jede Aktion minutengenau, um Doppel-Fütterungen auszuschließen!',
                'help_example': 'Bezeichnung: "Katze Futter geben" | Zuständig: "Sarah" | Uhrzeit: "07:30 Uhr". Nach dem Füttern loggst du es im Tracker ein.'
            },
            {
                'old_name': '🪴 Pflanzen-Pflege',
                'name': 'Pflanzen-Pflege',
                'icon': '🪴',
                'fields': {'use_tracker': True, 'use_reminder': True},
                'help_purpose': 'Perfekt, um das Gießen, Düngen und Umtopfen deiner Zimmerpflanzen strukturiert im Griff zu behalten.',
                'help_fields': 'Pflege deine Pflanzen optimal:\n• Gieß-Intervall (Erinnerung): Alle wie viele Tage gegossen wird (z.B. alle 7 Tage)\n• Gieß-Tracker: Logge das Gießen im Live-Tracker, um Staunässe sicher zu verhindern.',
                'help_example': 'Bezeichnung: "Monstera gießen" | Erinnerung: "Alle 8 Tage" | Tracker: Aktiviert. Sobald du mit der Gießkanne herumgehst, loggst du es ein!'
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
                    'use_end_date': False, 'use_persons': False, 'use_reminder': False,
                    'use_rating': False, 'use_tracker': False, 'use_milestone': False,
                    'use_url': False,
                    'help_purpose': data.get('help_purpose'),
                    'help_fields': data.get('help_fields'),
                    'help_example': data.get('help_example'),
                }
                full_fields.update(data['fields'])
                
                ListTemplate.objects.update_or_create(
                    category=cat,
                    defaults=full_fields
                )
                self.stdout.write(self.style.SUCCESS(f"Updated {cat.name} with icon {cat.icon} and help texts"))
