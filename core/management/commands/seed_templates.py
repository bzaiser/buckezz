from django.core.management.base import BaseCommand
from core.models import ListCategory, ListTemplate
from django.db import transaction
from django.utils.text import slugify

class Command(BaseCommand):
    help = 'Seeds sensible list templates and cleans up icons'

    def add_arguments(self, parser):
        parser.add_argument(
            '--database',
            default='default',
            help='Nominates a database to seed templates into.',
        )

    def handle(self, *args, **options):
        templates_data = [
            {
                'old_name': '🛒 Einkaufsliste',
                'name': 'Einkaufsliste',
                'icon': '🛒',
                'fields': {'logic_type': 'generic', 'use_amount': True, 'use_brand': True, 'use_shop': True, 'use_price': True},
                'help_purpose': 'Perfekt für deinen Wocheneinkauf, Vorratsbestellungen oder geplante Anschaffungen.',
                'help_fields': '🔄 WORKFLOW & MEHRWERT:\n1. Planen: Trage alle Artikel bequem ein. Du kannst Marke, bevorzugtes Geschäft und Preis direkt in der Zeile erfassen.\n2. Einkaufen: Hake gekaufte Artikel live im Supermarkt ab. Sie wandern automatisch nach unten.\n3. Budget-Kontrolle: Die Liste errechnet in Echtzeit die Zwischensumme aller offenen Artikel sowie die Gesamtsumme deiner Einkäufe!\n\n🗣️ SMART VOICE-INTEGRATION (ALEXA):\nDein Skill „meinen Eimer“ ist voll integriert und besitzt einen genialen deutschen Einkaufs-Parser! Du kannst Einkäufe direkt per Sprache auf diese Liste setzen. Sage einfach:\n• „Alexa, lege 5 Stück Butter für 2 Euro in meinen Eimer“\n• „Alexa, öffne meinen Eimer und setze Milch auf die Liste“\n• „Alexa, sag meinen Eimer ich brauche 2 Flaschen Olivenöl von Aldi“\n\nDer Parser erkennt vollautomatisch:\n• Menge (z.B. „5 Stück“, „2 Flaschen“)\n• Produkt (z.B. „Butter“, „Olivenöl“)\n• Geschäft (z.B. „von Aldi“)\n• Preis (z.B. „für 2 Euro“)\n... und ordnet alles blitzschnell und sauber deiner Einkaufsliste zu!\n\n🛠️ AKTIVE FELDER IN DIESER LISTE:\n• Bezeichnung: Der Name des Produkts\n• Menge: Anzahl oder Mengenangabe (z.B. "3" oder "1 Packung")\n• Marke: Zur präzisen Orientierung im Regal (z.B. "Oatly")\n• Geschäft: Wo das Produkt gekauft werden soll (z.B. "Rewe", "Aldi")\n• Preis: Einzelpreis des Artikels zur automatischen Preiskalkulation',
                'help_example': """Titel / Bezeichnung: Hafermilch (Barista Edition)

Menge: 4 Packungen

Marke: Oatly

Geschäft: Edeka (Hauptstraße)

Preis: 2,19 € pro Packung

Notizen: Steht meistens bei den haltbaren Milchprodukten im Gang 3. Bitte nur die graue Barista-Edition mitnehmen!"""
            },
            {
                'old_name': '✅ To-Do Liste',
                'name': 'To-Do Liste',
                'icon': '✅',
                'fields': {'logic_type': 'todo', 'use_end_date': True, 'use_persons': True, 'use_reminder': True},
                'help_purpose': 'Strukturierte Erfassung, Zuweisung und Überwachung all deiner privaten und beruflichen Aufgaben.',
                'help_fields': '🔄 WORKFLOW & MEHRWERT:\n1. Erfassen: Schreibe anstehende Aufgaben auf.\n2. Zuweisen & Planen: Bestimme Fälligkeiten und weise Aufgaben Familienmitgliedern oder Kollegen zu.\n3. Automatischer Wecker: Setze reisesichere E-Mail-Erinnerungen ein. Die Status-Badges zeigen dir direkt, ob eine E-Mail geplant (⏰) oder bereits verschickt (📩) wurde.\n\n🛠️ AKTIVE FELDER IN DIESER LISTE:\n• Bezeichnung: Was getan werden muss\n• Fälligkeitsdatum: Bis wann die Aufgabe erledigt sein muss\n• Erinnerung: Wunschzeitpunkt für den automatischen E-Mail-Wecker\n• Zuständig (Personen): Teilt Aufgaben bestimmten Personen zu',
                'help_example': """Titel / Bezeichnung: Wohnzimmer streichen (Wände & Decke)

Fälligkeitsdatum: Sonntag, 24.05.2026 bis 18:00 Uhr

⏰ Erinnerung am: Samstag, 23.05.2026 um 10:00 Uhr (damit noch Zeit zum Abkleben bleibt)

Zuständig: Jonas, Papa

Notizen: Abdeckfolie, Malerkrepp und weiße Wandfarbe (Alpina) vorher im Baumarkt besorgen. Papa bringt die Teleskopstange mit!"""
            },
            {
                'old_name': '🍷 Weinvorrat',
                'name': 'Weinvorrat',
                'icon': '🍷',
                'fields': {'logic_type': 'generic', 'use_amount': True, 'use_brand': True, 'use_location': True},
                'help_purpose': 'Präzise Bestandsübersicht über deinen Weinkeller, Gin-Regale, deine Hausbar oder Vorratskammer.',
                'help_fields': '🔄 WORKFLOW & MEHRWERT:\n1. Inventarisieren: Trage Flaschen mit Marke, Jahrgang und genauem Lagerort ein.\n2. Schneller Abgleich: Über die +/- Knöpfe direkt in der Liste kannst du die Mengen sekundenschnell anpassen, wenn du eine Flasche entnimmst oder einlagerst – ganz ohne die Zeile öffnen zu müssen!\n\n🛠️ AKTIVE FELDER IN DIESER LISTE:\n• Bezeichnung: Name des edlen Tropfens / Getränks\n• Menge: Aktueller Flaschenbestand (direkt in der Liste editierbar)\n• Winzer/Marke: Hersteller, Winzer oder Marke zur Orientierung\n• Lagerort: Wo genau sich das Produkt befindet (z.B. "Keller, Regal B")',
                'help_example': """Titel / Bezeichnung: Cabernet Sauvignon (Jahrgang 2019)

Menge: 4 Flaschen (von ursprünglich 6)

Winzer / Marke: Château Margaux

Lagerort: Weinkeller, Holzregal 3, Fach 5A

Notizen: Ein absoluter Spitzenwein. Sollte mindestens 2 Stunden vor dem Trinken dekantiert werden. Perfekt zu dunklem Fleisch oder reifem Käse."""
            },
            {
                'old_name': '🗓️ Veranstaltungsplaner',
                'name': 'Veranstaltungsplaner',
                'icon': '🗓️',
                'fields': {'logic_type': 'event', 'use_location': True, 'use_start_date': True, 'use_end_date': True, 'use_persons': True, 'use_price': True},
                'help_purpose': 'Umfassende Koordination von Geburtstagen, Hochzeiten, Supper Clubs, Grillfesten oder Business-Events.',
                'help_fields': '🔄 WORKFLOW & MEHRWERT:\n1. Planen: Erstelle Event-Posten (z.B. "Location mieten", "Catering organisieren").\n2. Supper Club & Einladungen: Markiere Einträge beim Erstellen als "Einladung". Dadurch werden alle Listen-Mitglieder automatisch als Gäste eingeladen und können ihren RSVP-Status (Zusage 🟢, Absage 🔴, Vielleicht ⚪) direkt in der Liste pflegen.\n3. Aufgaben & Handheben (🙋): Normale Posten (z.B. "Nudelsalat") zeigen einen "🙋 Übernehmen"-Button. Jedes Mitglied kann sich die Aufgabe mit einem Klick zuweisen (Status: Bringe ich mit! 🍻).\n4. Budget: Lege Preise fest – die Liste berechnet das Gesamtbudget automatisch.\n\n🛠️ AKTIVE FELDER IN DIESER LISTE:\n• Bezeichnung: Name der Aktivität / Planungs-Aufgabe\n• Ort: Veranstaltungsort oder Adresse\n• Start & Ende: Exakter Zeitraum für den Ablauf\n• Einladung: Aktiviert die RSVP-Gästeliste für diesen Eintrag\n• Zuständig (Personen): Zugewiesene Organisatoren / Helfer / Gäste\n• Kosten/Preis: Kalkulierter Einzelpreis zur automatischen Budgetberechnung',
                'help_example': """Titel / Bezeichnung: Bagels & mediterrane Dips besorgen

Ort: Bäckerei Schmidt / Feinkostladen

Start: Samstag, 20.06.2026 um 17:00 Uhr

Zuständig: Felix (Status: Bringe ich mit! 🍻)

Preis / Budget: 25,00 € (Gesamtkalkulation für Bagels und frischen Hummus)

Notizen: Felix hat über den "🙋 Übernehmen"-Button freiwillig die Hand gehoben. Bitte Kassenbon aufheben für die Umlage!"""
            },
            {
                'old_name': '💊 Medikamentenplan',
                'name': 'Medikamentenplan',
                'icon': '💊',
                'fields': {'logic_type': 'tracker', 'use_amount': True, 'use_start_date': True, 'use_persons': True, 'use_tracker': True, 'use_reminder': True},
                'help_purpose': 'Verlässliche Einnahmekontrolle, reisesichere Wecker und lückenlose Dokumentation deiner täglichen Medikamente.',
                'help_fields': '🔄 WORKFLOW & MEHRWERT:\n1. Dosierung & Wecker: Trage Medikamente, Dosis und Einnahmezeitpunkte ein. Der E-Mail-Wecker passt sich auf Reisen vollautomatisch deiner Ortszeit an.\n2. Live-Tracker: Klicke im intuitiven Einnahme-Tracker direkt auf "Eingenommen". Die Einnahme wird minutengenau im Verlauf mit Namen protokolliert.\n3. Sicherheit: Doppel-Einnahmen oder vergessene Dosen gehören der Vergangenheit an!\n\n🛠️ AKTIVE FELDER IN DIESER LISTE:\n• Bezeichnung: Name des Medikaments\n• Menge: Dosis pro Einnahme (z.B. "1 Tablette" oder "15 Tropfen")\n• Startdatum: Wann die Einnahme-Phase beginnt\n• Erinnerung: Zeitpunkt für deinen automatischen E-Mail-Wecker\n• Personen: Für wen das Medikament bestimmt ist\n• Tracker: Aktiviert das minutengenaue Live-Einnahmeprotokoll',
                'help_example': """Titel / Bezeichnung: Magnesium 400 (Hochdosiert gegen Wadenkrämpfe)

Dosierung / Menge: 1 Kapsel am Abend

Startdatum: Täglich ab dem 20.05.2026

⏰ Erinnerung am: Täglich um 20:00 Uhr (per E-Mail-Wecker, der sich auf Reisen automatisch anpasst)

Personen: Bernd

Live-Tracker: Aktiviert

Notizen: Immer mit ausreichend Wasser direkt nach dem Abendessen einnehmen. Nach dem Schlucken einfach im Live-Tracker auf "Eingenommen" klicken!"""
            },
            {
                'old_name': '🎬 Wunschliste',
                'name': 'Wunschliste',
                'icon': '🎬',
                'fields': {
                    'logic_type': 'gift',
                    'use_location': True,
                    'use_persons': True,
                    'use_beneficiary': True,
                    'use_secret_santa': True,
                    'use_is_public': True,
                    'use_allow_public_edit': True
                },
                'help_purpose': 'Smarte Verwaltung von Geschenken und Wünschen für Geburtstage, Weihnachten oder Hochzeiten – mit eingebautem Überraschungs-Schutz!',
                'help_fields': '🔄 DER GENIALE WICHTEL- & ÜBERRASCHUNGS-WORKFLOW:\n1. Wünsche äußern: Das Geburtstagskind erstellt seine Wünsche mit Shop-Links und Bildern.\n2. Teilen: Sende den Wichtel-Link der Liste an deine Freunde/Gäste.\n3. Reservieren & Schenken: Gäste können Wünsche auf "Reserviert" (🔒) oder "Erfüllt" (🎁) setzen und sich eintragen. \n4. Der Clou (Überraschungs-Schutz!): Das Geburtstagskind sieht die Reservierungen und Zuordnungen NICHT! Für den Beschenkten bleibt alles offen und spannend. Nur die schenkenden Gäste sehen untereinander, wer was besorgt, um Doppelkäufe komplett auszuschließen!\n\n🛠️ AKTIVE FELDER IN DIESER LISTE:\n• Bezeichnung: Name des Wunsches\n• Geschäft/Link (Ort): Shop-Name oder Direkt-URL zum Bestellen (wird unter "Ort" erfasst)\n• Beschenkter (Personen): Für wen der Wunsch gedacht ist (wird unter "Personen" erfasst)',
                'help_example': """Titel / Bezeichnung: Acoustic Western-Gitarre (Harley Benton)

Geschäft / Shoplink: www.thomann.de/de/harley_benton_custom_line.htm

Wunsch von: Sarah (Geburtstagswunsch)

Notizen: Sarah wünscht sich diese Gitarre schon sehr lange zum Üben. Wenn reserviert oder gekauft, bitte den Status hier im Wichtel-Link direkt auf "Reserviert" oder "Erfüllt" ändern – Sarah sieht davon nichts, aber wir vermeiden doppelte Geschenke!"""
            },
            {
                'old_name': '🏆 Winliste',
                'name': 'Winliste',
                'icon': '🏆',
                'fields': {'logic_type': 'generic', 'use_rating': True, 'use_persons': True},
                'help_purpose': 'Dein persönliches Dankbarkeitstagebuch zum Sammeln positiver Momente, Erfolge und Meilensteine.',
                'help_fields': '🔄 WORKFLOW & MEHRWERT:\n1. Erfolge feiern: Halte bestandene Prüfungen, sportliche Siege oder einfach schöne Erlebnisse fest.\n2. Bewerten: Verteile 1-5 Sterne je nach persönlicher Bedeutung und emotionalem Wert.\n3. Teilen: Halte fest, mit wem du diese glücklichen Momente geteilt hast, um an grauen Tagen positive Energie zu tanken.\n\n🛠️ AKTIVE FELDER IN DIESER LISTE:\n• Bezeichnung: Das erfreuliche Ereignis\n• Bedeutung (Bewertung): Emotionale Wichtigkeit von 1-5 Sternen\n• Geteilt mit (Personen): Mit wem du diesen Moment erlebt hast',
                'help_example': """Titel / Bezeichnung: Bachelorarbeit im Fach Informatik erfolgreich bestanden!

Bedeutung (Bewertung): ⭐⭐⭐⭐⭐ (Absolutes Lebens-Highlight!)

Dabei gewesene Personen: Familie, Sarah, meine besten Freunde

Notizen: Note 1.3 erhalten! Die monatelange harte Arbeit in der Bibliothek hat sich endlich ausgezahlt. Danach gab es ein grandioses Abendessen beim Italiener zur Feier des Tages. Nie den Glauben an sich selbst verlieren!"""
            },
            {
                'old_name': '🎯 Bucket List',
                'name': 'Bucket List',
                'icon': '🎯',
                'fields': {'logic_type': 'bucket', 'use_milestone': True, 'use_url': True, 'use_rating': True},
                'help_purpose': 'Planung, Visualisierung und Festhalten all deiner großen Lebensträume, Abenteuer und Reiseziele.',
                'help_fields': '🔄 WORKFLOW & MEHRWERT:\n1. Träumen: Schreibe Lebensziele auf (z.B. "Fallschirmsprung machen", "Polarlichter sehen").\n2. Strukturieren: Ordne deine Träume Meilensteinen zu (z.B. "vor 30", "vor 50") und bewerte ihre Wichtigkeit.\n3. Realisieren & Dokumentieren: Verlinke Infos oder Reiseberichte. Wenn du ein Ziel erreichst, hake es ab. Das "Erreicht am"-Datum bleibt editierbar, um deine Lebens-Chronik perfekt zu pflegen!\n\n🛠️ AKTIVE FELDER IN DIESER LISTE:\n• Bezeichnung: Dein Lebensziel / Abenteuer\n• Lebensabschnitt (Milestone): Wann du es erreichen möchtest\n• Wichtigkeit (Bewertung): Bedeutung des Traums von 1-5 Sternen\n• Inspirations-Link (URL): Hilfreicher Link oder Bild-URL zum Traum',
                'help_example': """Titel / Bezeichnung: Spektakulärer Tandem-Fallschirmsprung aus 4.000 Metern Höhe

Milestone / Lebensabschnitt: Vor dem 40. Geburtstag erreichen!

Wichtigkeit (Bewertung): ⭐⭐⭐⭐⭐ (Absoluter Adrenalinkick-Traum)

Inspirations-Link (URL): www.skydiving-school-bavaria.de

Notizen: Am besten im Sommer bei klarem Himmel buchen. Die GoPro-Video-Option unbedingt mitbestellen, um den freien Fall als Erinnerung festzuhalten!"""
            },
            {
                'old_name': '🐾 Haustier-Planer',
                'name': 'Haustier-Planer',
                'icon': '🐾',
                'fields': {'logic_type': 'tracker', 'use_persons': True, 'use_tracker': True, 'use_reminder': True},
                'help_purpose': 'Gemeinsame Koordination und lückenlose Abstimmung der Fütterung, Pflege und Medizin deiner Haustiere im Haushalt.',
                'help_fields': '🔄 WORKFLOW & MEHRWERT:\n1. Absichern: Trage Pflege- und Fütterungs-Aufgaben ein.\n2. Erinnern: Nutze reisesichere E-Mail-Wecker für regelmäßige Behandlungen oder Arztbesuche.\n3. Live-Tracker: Protokolliere jede Fütterung oder Gassirunde live mit einem Klick. Alle Haushaltsmitglieder sehen sofort in Echtzeit, ob die Katze oder der Hund bereits gefüttert wurde – Doppel-Fütterungen ausgeschlossen!\n\n🛠️ AKTIVE FELDER IN DIESER LISTE:\n• Bezeichnung: Pflege-Aufgabe (z.B. "Katze füttern", "Medizin geben")\n• Zuständigkeit (Personen): Wer die Aufgabe übernimmt\n• Erinnerung: Uhrzeit für den automatischen E-Mail-Wecker\n• Tracker: Live-Protokollierung zur Abstimmung im Haushalt',
                'help_example': """Titel / Bezeichnung: Katze Minka - Nassfutter geben (Morgen-Portion)

Zuständig: Sarah

⏰ Erinnerung am: Täglich um 07:30 Uhr (damit Minka nicht hungert)

Pflege-Tracker: Aktiviert (Protokollierung in Echtzeit)

Notizen: Bitte nur eine halbe Dose vom Geflügel-Nassfutter geben. Falls sie die Medizin nehmen muss, diese unter das Futter mischen. Nach dem Füttern sofort im Tracker abhaken, damit Papa nicht versehentlich nochmals füttert!"""
            },
            {
                'old_name': '🪴 Pflanzen-Pflege',
                'name': 'Pflanzen-Pflege',
                'icon': '🪴',
                'fields': {'logic_type': 'tracker', 'use_tracker': True, 'use_reminder': True},
                'help_purpose': 'Strukturierte und disziplinierte Pflege deiner Zimmerpflanzen – verhindert Übergießen und Austrocknen.',
                'help_fields': '🔄 WORKFLOW & MEHRWERT:\n1. Strukturieren: Erfasse deine Pflanzen und bestimme ihre individuellen Gieß- und Dünge-Intervalle.\n2. Gießen & Düngen: Der reisesichere E-Mail-Wecker erinnert dich an das fällige Intervall.\n3. Protokollieren: Trage das Gießen direkt über das Live-Tracker-Panel ein, um die Gießhistorie im Blick zu behalten und Staunässe sicher zu verhindern!\n\n🛠️ AKTIVE FELDER IN DIESER LISTE:\n• Bezeichnung: Name der Zimmerpflanze (z.B. "Monstera")\n• Intervall (Erinnerung): Wann das nächste Gießen fällig ist\n• Tracker: Live-Gießprotokoll zum schnellen Abhaken nach dem Gießen',
                'help_example': """Titel / Bezeichnung: Große Monstera (Fensterblatt) im Wohnzimmer gießen

Intervall / Erinnerung: Alle 8 Tage am Morgen

Gieß-Tracker: Aktiviert (zur optimalen Gieß-Kontrolle)

Notizen: Ca. 300ml lauwarmes, abgestandenes Wasser gießen. Vor dem Gießen mit dem Finger prüfen, ob die obere Erdschicht trocken ist (Staunässe vermeiden!). Blätter gelegentlich mit Wasser besprühen und abstauben."""
            },
            {
                'old_name': 'Arzt Termine',
                'name': 'Arzt Termine',
                'icon': '🏥',
                'fields': {
                    'logic_type': 'generic',
                    'use_brand': True,
                    'use_start_date': True,
                    'use_reminder': True,
                    'use_location': True,
                    'use_rating': True
                },
                'help_purpose': 'Strukturierte Übersicht, rechtzeitige Erinnerung und lückenlose Nachbereitung all deiner Arzt- und Vorsorgetermine.',
                'help_fields': '🔄 WORKFLOW & MEHRWERT:\n1. Terminieren: Trage Arztbesuche mit Fachbereich, genauer Uhrzeit, Praxisname und Adresse weit im Voraus ein.\n2. Rechtzeitig erinnern: Der E-Mail-Wecker erinnert dich rechtzeitig vor dem Termin, damit du wichtige Unterlagen oder Vorbereitungen nicht vergisst.\n3. Dokumentieren & Priorisieren: Nutze die Wichtigkeits-Sterne für dringende Termine und halte Telefonnummern für Rückfragen direkt griffbereit.\n\n🛠️ AKTIVE FELDER IN DIESER LISTE:\n• Bezeichnung: Anlass / Fachbereich des Termins (z.B. "Zahnarzt Vorsorge")\n• Arzt/Praxis (Name): Name des Arztes oder der Praxis (wird im Feld "Marke" erfasst)\n• Termin (Start): Genaue Uhrzeit des Arzttermins\n• Erinnerung: Wunschzeitpunkt für deinen automatischen E-Mail-Wecker\n• Ort/Telefon: Praxisadresse und Telefonnummer zur schnellen Kontaktaufnahme\n• Bewertung (Bedeutung): Dringlichkeit des Termins oder Beurteilung des Arztes von 1-5 Sternen',
                'help_example': 'Titel / Bezeichnung: Augenarzt\n\nMarke: Sima\n\nOrt: Freiberg\n\nBewertung: ⭐⭐⭐⭐\n\nStart: 19.11.2026 09:10 zu diesem Zeitpunkt findet der Arzttermin statt.\n\n⏰ Erinnerung am: 14.10.2026 22:19 Wann willst du eine Erinnerung erhalten?\n\nNotizen: Zum Beispiel Mit Fahrer kommen da die Augen getropft werden'
            },
            {
                'old_name': '🏋️‍♂️ Trainingsplan',
                'name': 'Trainingsplan',
                'icon': '🏋️‍♂️',
                'fields': {
                    'logic_type': 'workout',
                    'use_rating': True
                },
                'help_purpose': 'Voll-polymorpher Trainingsplaner für Fitnessstudio, Laufen, Radsport, HIIT und Crossfit.',
                'help_fields': '🔄 WORKFLOW & MEHRWERT:\n1. Planen: Erstelle Übungen oder Läufe. Wähle den Aktivitätstyp (Kraft, Ausdauer oder Intervall/HIIT).\n2. Aktiv Trainieren: Öffne das Workout-Cockpit (Play-Icon). Die interaktive Stoppuhr, der Satz-Erledigungs-Haken, der automatische Pausen-Countdown mit Beep-Signal und der Rundenzeit-Stopper begleiten dich live im Gym oder auf der Laufstrecke!\n3. Progression & Historie: Dokumentiere jede Trainingseinheit mit Gesamtbewertung, Stimmung und Notizen. Dein gesamter Leistungsverlauf wird lückenlos historisch protokolliert, um Fortschritte auszuwerten!\n\n🛠️ AKTIVE FELDER IN DIESER LISTE:\n• Bezeichnung: Name der Übung, der Laufstrecke oder des WODs (z.B. "Bankdrücken")\n• Aktivitätstyp: Kraft (Gewichte/Sätze), Ausdauer (Kilometer/Zeit) oder Intervall (Crossfit/HIIT)\n• Konfiguration: Sätze, Ziel-Wiederholungen/Gewicht oder Distanz/Zeit-Ziele\n• Bewertung & Notizen: Zur Protokollierung deines körperlichen Befindens am Ende des Workouts',
                'help_example': """Aktivitätstyp: Krafttraining (strength)
Übung / Bezeichnung: Bankdrücken
Satz 1: 10 Wiederholungen mit 50 kg
Satz 2: 8 Wiederholungen mit 60 kg
Satz 3: 5 Wiederholungen mit 70 kg
Pause nach Sätzen: 3 Minuten (180s)
Rest-Timer: Aktiviert

Notizen: Beim letzten Satz bis zum Muskelversagen gegangen. Nächstes Mal versuchen, das Gewicht beim 2. Satz um 2.5 kg zu erhöhen!"""
            }
        ]

        db = options.get('database', 'default')
        with transaction.atomic(using=db):
            for data in templates_data:
                # Try to find by old name or new name
                cat = ListCategory.objects.using(db).filter(name__in=[data.get('old_name'), data['name']]).first()
                if not cat:
                    cat = ListCategory.objects.using(db).create(name=data['name'], slug=slugify(data['name']))
                
                cat.name = data['name']
                cat.icon = data['icon']
                cat.slug = slugify(data['name'])
                cat.save(using=db)
                
                full_fields = {
                    'logic_type': 'generic',
                    'use_amount': False, 'use_brand': False, 'use_shop': False,
                    'use_price': False, 'use_location': False, 'use_start_date': False,
                    'use_end_date': False, 'use_persons': False, 'use_reminder': False,
                    'use_rating': False, 'use_tracker': False, 'use_milestone': False,
                    'use_url': False, 'use_is_public': False, 'use_allow_public_edit': False,
                    'use_beneficiary': False, 'use_secret_santa': False,
                    'help_purpose': data.get('help_purpose'),
                    'help_fields': data.get('help_fields'),
                    'help_example': data.get('help_example'),
                }
                full_fields.update(data['fields'])
                
                ListTemplate.objects.using(db).update_or_create(
                    category=cat,
                    defaults=full_fields
                )
                self.stdout.write(self.style.SUCCESS(f"Updated {cat.name} with icon {cat.icon} and help texts in database '{db}'"))
