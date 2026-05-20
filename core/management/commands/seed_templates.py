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
                'help_fields': 'Wenn du diese Liste wählst, stehen dir folgende nützliche Felder zur Verfügung:\n• Bezeichnung: Name des Artikels\n• Menge: Menge oder Packungsanzahl (z.B. "3" oder "1 Packung")\n• Marke: Produkt-Marke zur genauen Orientierung\n• Geschäft: Wo du den Artikel kaufen möchtest (z.B. "Rewe", "Aldi")\n• Preis: Einzelpreis des Artikels zur automatischen Berechnung der Summe',
                'help_example': 'Titel / Bezeichnung: Hafermilch\nMenge: 4 Packungen\nMarke: Oatly\nGeschäft: Edeka\nPreis: 1.99 €'
            },
            {
                'old_name': '✅ To-Do Liste',
                'name': 'To-Do Liste',
                'icon': '✅',
                'fields': {'use_end_date': True, 'use_persons': True, 'use_reminder': True},
                'help_purpose': 'Strukturierte Erfassung all deiner privaten und beruflichen Aufgaben.',
                'help_fields': 'Nutze folgende Felder zur Aufgabenverwaltung:\n• Bezeichnung: Was getan werden muss\n• Fälligkeitsdatum: Bis wann die Aufgabe erledigt sein muss\n• Erinnerung: Stelle E-Mail-Wecker ein. Auf Reisen passt sich die Zeit automatisch an (z.B. in Griechenland). Du siehst den Status direkt am Symbol (⏰ = geplant, 📩 = gesendet!)\n• Personen: Weise Aufgaben deinen Freunden oder Familienmitgliedern zu!',
                'help_example': 'Titel / Bezeichnung: Wohnzimmer streichen\nFälligkeitsdatum: Sonntag\nErinnerung: Samstag, 10:00 Uhr\nBeteiligte Personen: Jonas, Papa'
            },
            {
                'old_name': '🍷 Weinvorrat',
                'name': 'Weinvorrat',
                'icon': '🍷',
                'fields': {'use_amount': True, 'use_brand': True, 'use_location': True},
                'help_purpose': 'Perfekt, um die Übersicht über deinen Weinkeller, Gin-Regale oder deine Hausbar zu behalten.',
                'help_fields': 'Verwalte deine Bestände mit diesen Feldern:\n• Bezeichnung: Name des Getränks\n• Menge: Aktuelle Anzahl an Flaschen (kann in der Liste direkt editiert werden!)\n• Winzer/Marke: Name des Herstellers oder Weinguts\n• Lagerort: Wo genau die Flasche liegt (z.B. "Kellerregal 3, Fach B")',
                'help_example': 'Titel / Bezeichnung: Cabernet Sauvignon 2019\nMenge: 4 Flaschen\nWinzer/Marke: Château Margaux\nLagerort: Fach 5A'
            },
            {
                'old_name': '🗓️ Veranstaltungsplaner',
                'name': 'Veranstaltungsplaner',
                'icon': '🗓️',
                'fields': {'use_location': True, 'use_start_date': True, 'use_end_date': True, 'use_persons': True, 'use_price': True},
                'help_purpose': 'Perfekt für Geburtstage, Ausflüge, Grillfeste oder Business-Events.',
                'help_fields': 'Koordiniere deine Feiern mit diesen Feldern:\n• Bezeichnung: Name der Aktivität / des Postens\n• Ort: Wo die Feier oder Aktion stattfindet\n• Start & Ende: Genaue Veranstaltungszeiträume\n• Beteiligte Personen: Ordne Aufgaben oder Rollen bestimmten Personen zu\n• Kosten/Budget: Kalkulierte Preise pro Planungs-Posten zur Budgetkontrolle',
                'help_example': 'Titel / Bezeichnung: Getränke holen\nOrt: Getränkemarkt Müller\nStart: 18.06.2026 15:00 Uhr\nEnde: 18.06.2026 16:30 Uhr\nZuständig: Felix\nPreis: 60.00 €'
            },
            {
                'old_name': '💊 Medikamentenplan',
                'name': 'Medikamentenplan',
                'icon': '💊',
                'fields': {'use_amount': True, 'use_start_date': True, 'use_persons': True, 'use_tracker': True, 'use_reminder': True},
                'help_purpose': 'Verlässliche Erinnerung und Dokumentation deiner täglichen Medikamente.',
                'help_fields': 'Behalte deine Gesundheit im Griff:\n• Bezeichnung: Name des Medikaments\n• Dosierung/Menge: Menge oder Tabletten-Anzahl pro Einnahme (z.B. "1 Tablette")\n• Startdatum: Wann die Einnahme-Phase beginnt\n• Erinnerung: E-Mail-Wecker, die sich auf Reisen vollautomatisch an deinen Standort anpassen (z.B. in Griechenland). Status: ⏰ = geplant, 📩 = gesendet.\n• Personen: Für wen das Medikament bestimmt ist\n• Einnahme-Tracker: Protokolliere Einnahmen in Echtzeit mit einem Klick im Live-Tracker!',
                'help_example': 'Titel / Bezeichnung: Magnesium 400\nMenge: 1 Kapsel\nStartdatum: Täglich ab 20.05.2026\nErinnerung: Täglich um 20:00 Uhr\nPersonen: Bernd\nLive-Tracker: Aktiv (Nach dem Schlucken klickst du einfach auf "Eingenommen")'
            },
            {
                'old_name': '🎬 Wunschliste',
                'name': 'Wunschliste',
                'icon': '🎬',
                'fields': {'use_location': True, 'use_persons': True},
                'help_purpose': 'Geschenkideen für Geburtstage, Weihnachten oder Hochzeiten sammeln und verteilen.',
                'help_fields': 'Halte Geschenkideen fest:\n• Bezeichnung: Name des Geschenks\n• Geschäft/Link (Ort): Wo man den Wunsch kaufen kann (wird im Feld "Ort" erfasst)\n• Wünschende Person: Für wen das Geschenk gedacht ist (wird im Feld "Personen" erfasst)',
                'help_example': 'Titel / Bezeichnung: Acoustic Guitar\nGeschäft/Link (Ort): Thomann.de\nWunsch von (Personen): Sarah'
            },
            {
                'old_name': '🏆 Winliste',
                'name': 'Winliste',
                'icon': '🏆',
                'fields': {'use_rating': True, 'use_persons': True},
                'help_purpose': 'Positive Erlebnisse, bestandene Prüfungen oder sportliche Meilensteine als Motivation sammeln.',
                'help_fields': 'Dokumentiere deine Siege:\n• Bezeichnung: Das erfreuliche Erlebnis\n• Bedeutung (Bewertung): Bewerte das Erlebnis von 1-5 Sternen zur Motivation\n• Geteilt mit (Personen): Wer war an diesem glücklichen Tag dabei?',
                'help_example': 'Titel / Bezeichnung: Bachelorarbeit bestanden (1.3)\nBedeutung (Bewertung): ⭐⭐⭐⭐⭐\nDabei (Personen): Familie, Freunde'
            },
            {
                'old_name': '🎯 Bucket List',
                'name': 'Bucket List',
                'icon': '🎯',
                'fields': {'use_milestone': True, 'use_url': True, 'use_rating': True},
                'help_purpose': 'Träume, Abenteuer und Lebensziele planen und festhalten.',
                'help_fields': 'Plane deine Lebensziele:\n• Bezeichnung: Dein Traum oder Abenteuer\n• Lebensabschnitt (Milestone): Wann willst du es erreichen? (z.B. "vor 30", "vor 60")\n• Wichtigkeit (Bewertung): Bedeutung des Traums von 1-5 Sternen\n• Inspirations-Link (URL): Link mit Reiseinfos oder Bildern',
                'help_example': 'Titel / Bezeichnung: Fallschirmsprung machen\nMilestone: vor 40\nWichtigkeit (Bewertung): ⭐⭐⭐⭐⭐\nLink (URL): skydiving-school.de'
            },
            {
                'old_name': '🐾 Haustier-Planer',
                'name': 'Haustier-Planer',
                'icon': '🐾',
                'fields': {'use_persons': True, 'use_tracker': True, 'use_reminder': True},
                'help_purpose': 'Perfekt, um die Versorgung von Hund, Katze, Vögeln oder Pferd im Haushalt abzustimmen.',
                'help_fields': 'Organisiere die Tierpflege:\n• Bezeichnung: Pflege-Aufgabe\n• Zuständigkeit (Personen): Wer füttert das Tier oder geht Gassi?\n• Erinnerung: E-Mail-Wecker für Medizin, Bürsten, etc. (mit automatischer Zeitzonen-Erkennung auf Reisen: ⏰ = geplant, 📩 = gesendet)\n• Pflege-Tracker: Logge jede Aktion minutengenau, um Doppel-Fütterungen auszuschließen!',
                'help_example': 'Titel / Bezeichnung: Katze Minka Futter geben\nZuständig (Personen): Sarah\nErinnerung: Täglich 07:30 Uhr\nPflege-Tracker: Aktiv'
            },
            {
                'old_name': '🪴 Pflanzen-Pflege',
                'name': 'Pflanzen-Pflege',
                'icon': '🪴',
                'fields': {'use_tracker': True, 'use_reminder': True},
                'help_purpose': 'Perfekt, um das Gießen, Düngen und Umtopfen deiner Zimmerpflanzen strukturiert im Griff zu behalten.',
                'help_fields': 'Pflege deine Pflanzen optimal:\n• Bezeichnung: Name der Pflanze\n• Gieß-Intervall (Erinnerung): Wecker zum Gießen (reisesicher mit automatischer Zeitzone: ⏰ = geplant, 📩 = gesendet)\n• Gieß-Tracker: Logge das Gießen im Live-Tracker, um Staunässe sicher zu verhindern.',
                'help_example': 'Titel / Bezeichnung: Monstera gießen\nErinnerung: Alle 8 Tage\nGieß-Tracker: Aktiv'
            },
            {
                'old_name': 'Arzt Termine',
                'name': 'Arzt Termine',
                'icon': '🏥',
                'fields': {
                    'use_brand': True,
                    'use_start_date': True,
                    'use_reminder': True,
                    'use_location': True,
                    'use_rating': True
                },
                'help_purpose': 'Erfasse deine Arzt- und Vorsorgetermine strukturiert und behalte den Überblick über deine Gesundheit.',
                'help_fields': 'Perfekte Übersicht für deine Arztbesuche:\n• Bezeichnung: Fachbereich oder Anlass des Termins\n• Arzt/Praxis (Name): Name des Arztes, der Praxis oder des Fachgebiets (wird im Feld "Marke" erfasst)\n• Termin (Start): Genaue Uhrzeit des Arzttermins (z.B. "19.11.2026 09:10")\n• Erinnerung: Stelle Benachrichtigungen ein, um Fristen nicht zu verschlafen (reisesicher mit automatischer Zeitzone: ⏰ = geplant, 📩 = gesendet)\n• Ort/Telefon: Adresse des Arztes und eventuell die Telefonnummer zur direkten Kontaktaufnahme\n• Bewertung (Bedeutung): Drücke hier entweder deine Beurteilung des Arztes oder die Dringlichkeit/Wichtigkeit des Termins aus',
                'help_example': 'Titel / Bezeichnung: Augenarzt\n\nMarke: Sima\n\nOrt: Freiberg\n\nBewertung: ⭐⭐⭐⭐\n\nStart: 19.11.2026 09:10 zu diesem Zeitpunkt findet der Arzttermin statt.\n\n⏰ Erinnerung am: 14.10.2026 22:19 Wann willst du eine Erinnerung erhalten?\n\nNotizen: Zum Beispiel Mit Fahrer kommen da die Augen getropft werden'
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
