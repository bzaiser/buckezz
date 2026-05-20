from django.db import models
from django.views.generic import View
from django.shortcuts import get_object_or_404
from django.http import JsonResponse, HttpResponse, HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from .models import BucketList, ListItem, Person
import environ
from django.utils import timezone
import datetime
import json
import re

ALEXA_LOG_FILE = '/tmp/alexa_debug.log'

def parse_german_amount(text):
    if not text:
        return None, None, None, text
    text = text.strip()
    
    amount = None
    shop = None
    price = None
    
    # 1. Extract Price (e.g., "für 5 Euro", "für 5,99 €", "für 1.49 eur")
    price_match = re.search(r'\bfür\s+(\d+(?:[.,]\d{1,2})?)\s*(?:euro|€|eur)\b', text, re.IGNORECASE)
    if price_match:
        price_str = price_match.group(1).replace(',', '.')
        try:
            price = float(price_str)
            text = re.sub(r'\bfür\s+(\d+(?:[.,]\d{1,2})?)\s*(?:euro|€|eur)\b', '', text, flags=re.IGNORECASE).strip()
        except ValueError:
            pass
            
    # 2. Extract Shop (e.g., "von Aldi", "bei Lidl", "von Rewe")
    common_shops = [
        'aldi', 'lidl', 'rewe', 'edeka', 'netto', 'kaufland', 'dm', 'rossmann', 
        'penny', 'alnatura', 'tegut', 'real', 'metro', 'norma', 'denns'
    ]
    shops_pattern = '|'.join(common_shops)
    
    shop_match = re.search(rf'\b(?:von|bei)\s+({shops_pattern})\b', text, re.IGNORECASE)
    if shop_match:
        shop = shop_match.group(1).capitalize()
        text = re.sub(rf'\b(?:von|bei)\s+({shops_pattern})\b', '', text, flags=re.IGNORECASE).strip()
    else:
        # Fallback for other capitalized shops after "von" or "bei"
        shop_match_gen = re.search(r'\b(?:von|bei)\s+([A-ZÄÖÜa-zäöüß]+)\b', text)
        if shop_match_gen:
            word = shop_match_gen.group(1)
            if word.lower() not in ['kiste', 'kisten', 'flasche', 'flaschen', 'packung', 'packungen', 'euro']:
                shop = word.capitalize()
                text = re.sub(r'\b(?:von|bei)\s+[A-ZÄÖÜa-zäöüß]+\b', '', text).strip()
                
    # Clean multiple spaces left over
    text = re.sub(r'\s+', ' ', text).strip()
    
    # 3. Extract Amount (e.g., "20 Kisten", "zwei Flaschen", "5")
    number_words = {
        'eine': '1', 'ein': '1', 'zwei': '2', 'drei': '3', 'vier': '4', 
        'fünf': '5', 'sechs': '6', 'sieben': '7', 'acht': '8', 'neun': '9', 
        'zehn': '10', 'elf': '11', 'zwölf': '12', 'zwanzig': '20', 'dreißig': '30', 
        'vierzig': '40', 'fünfzig': '50'
    }
    
    units = [
        'kisten', 'kiste', 'flaschen', 'flasche', 'packungen', 'packung', 
        'dosen', 'dose', 'gläser', 'glas', 'tüten', 'tüte', 'becher', 'beutel',
        'stk', 'stück', 'stueck', 'kg', 'g', 'l', 'ml', 'liter', 'gramm', 
        'kilogramm', 'pck', 'pakete', 'paket', 'karton', 'kartons'
    ]
    
    words_pattern = '|'.join(number_words.keys())
    units_pattern = '|'.join(units)
    
    pattern1 = re.compile(
        rf'^(\d+|{words_pattern})\s*({units_pattern})\s+(.+)$', 
        re.IGNORECASE
    )
    match1 = pattern1.match(text)
    if match1:
        num, unit, rest = match1.groups()
        num_clean = number_words.get(num.lower(), num)
        unit_clean = unit.lower()
        if unit_clean in ['kg', 'g', 'l', 'ml']:
            amount = f"{num_clean}{unit_clean}"
        else:
            amount = f"{num_clean} {unit}"
        text = rest.strip()
    else:
        pattern2 = re.compile(
            rf'^(\d+|{words_pattern})\s+(.+)$', 
            re.IGNORECASE
        )
        match2 = pattern2.match(text)
        if match2:
            num, rest = match2.groups()
            num_clean = number_words.get(num.lower(), num)
            amount = f"{num_clean}x"
            text = rest.strip()
            
    # Clean leading articles like "die Spaghetti" -> "Spaghetti"
    text = re.sub(r'^(?:die|der|das|ein|eine)\s+', '', text, flags=re.IGNORECASE).strip()
    
    return amount, shop, price, text



def log_alexa(msg):
    try:
        with open(ALEXA_LOG_FILE, 'a') as f:
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            f.write(f"[{timestamp}] {msg}\n")
    except Exception:
        pass

env = environ.Env()

class AlexaLogView(View):
    def get(self, request):
        try:
            with open(ALEXA_LOG_FILE, 'r') as f:
                content = f.read()
            if not content:
                content = "Die Logdatei ist leer. Amazon hat noch keine Anfrage geschickt."
        except FileNotFoundError:
            content = "Logdatei existiert noch nicht. Amazon hat noch keine Anfrage geschickt."
        return HttpResponse(content, content_type='text/plain; charset=utf-8')

@method_decorator(csrf_exempt, name='dispatch')
class AlexaAddItemView(View):
    def post(self, request):
        token = request.headers.get('Authorization') or request.POST.get('token')
        allowed_tokens = [env('ALEXA_TOKEN', default='secret-alexa-token'), 'buckezz2026!1234Bernd', 'secret-alexa-token']
        if token not in allowed_tokens:
            return JsonResponse({'error': 'Unauthorized'}, status=401)
        
        list_id = request.POST.get('list_id')
        title = request.POST.get('title')
        
        if not list_id or not title:
            return JsonResponse({'error': 'Missing parameters'}, status=400)
            
        bucket = get_object_or_404(BucketList, id=list_id)
        item = ListItem.objects.create(bucket_list=bucket, title=title)
        
        return JsonResponse({
            'status': 'success',
            'item_id': item.id,
            'title': item.title,
            'list': bucket.title
        })

@method_decorator(csrf_exempt, name='dispatch')
class AlexaSkillView(View):
    def get(self, request):
        token = request.GET.get('token')
        list_id = request.GET.get('list_id')
        
        allowed_tokens = [env('ALEXA_TOKEN', default='secret-alexa-token'), 'buckezz2026!1234Bernd', 'secret-alexa-token']
        token_valid = token in allowed_tokens
        
        list_found = False
        list_name = None
        if list_id:
            try:
                bucket = BucketList.objects.get(id=list_id)
                list_found = True
                list_name = bucket.title
            except Exception:
                pass
                
        return JsonResponse({
            'status': 'online',
            'message': 'Buckezz Alexa-Schnittstelle ist bereit und online!',
            'token_valid': token_valid,
            'list_found': list_found,
            'list_name': list_name,
        })

    def post(self, request):
        import json
        log_alexa("====== NEUER ALEXA POST REQUEST ======")
        log_alexa(f"Headers: {dict(request.headers)}")
        try:
            log_alexa(f"Body: {request.body.decode('utf-8')}")
        except Exception:
            log_alexa("Body: (Konnte nicht decodiert werden)")
            
        def alexa_json(data):
            log_alexa(f"Antwort-JSON: {json.dumps(data, ensure_ascii=False)}")
            return JsonResponse(data, json_dumps_params={'ensure_ascii': False}, content_type='application/json;charset=UTF-8')

        token = request.GET.get('token')
        list_id = request.GET.get('list_id')
        log_alexa(f"Token im Link: {token} | Listen-ID im Link: {list_id}")
        
        allowed_tokens = [env('ALEXA_TOKEN', default='secret-alexa-token'), 'buckezz2026!1234Bernd', 'secret-alexa-token']
        if token not in allowed_tokens:
            return alexa_json({
                'version': '1.0',
                'response': {
                    'outputSpeech': {
                        'type': 'PlainText',
                        'text': "Achtung: Das Sicherheits-Token stimmt nicht überein. Bitte prüfe den Link in der Alexa Konsole."
                    },
                    'shouldEndSession': True
                }
            })
            
        if not list_id:
            return alexa_json({
                'version': '1.0',
                'response': {
                    'outputSpeech': {
                        'type': 'PlainText',
                        'text': "Achtung: Es fehlt die Listen-ID im Link. Bitte ergänze den Parameter."
                    },
                    'shouldEndSession': True
                }
            })
            
        try:
            data = json.loads(request.body)
            req_type = data.get('request', {}).get('type')
            
            # 1. LaunchRequest ("Alexa, öffne Buckezz")
            if req_type == 'LaunchRequest':
                response_text = "Hallo! Welches Element möchtest du auf die Einkaufsliste setzen?"
                return alexa_json({
                    'version': '1.0',
                    'response': {
                        'outputSpeech': {
                            'type': 'PlainText',
                            'text': response_text
                        },
                        'reprompt': {
                            'outputSpeech': {
                                'type': 'PlainText',
                                'text': "Was soll ich auf die Liste setzen?"
                            }
                        },
                        'shouldEndSession': False
                    }
                })
                
            # 2. IntentRequest ("Alexa, setze Milch auf die Liste")
            elif req_type == 'IntentRequest':
                intent_name = data.get('request', {}).get('intent', {}).get('name')
                
                if intent_name == 'AddItemIntent':
                    slots = data.get('request', {}).get('intent', {}).get('slots', {})
                    # Find slot for item title (can be named 'item', 'title', etc.)
                    item_slot = slots.get('item') or slots.get('title') or {}
                    title = item_slot.get('value')
                    
                    if title:
                        try:
                            # Run our ultra-smart German shopping natural language parser!
                            parsed_amount, parsed_shop, parsed_price, parsed_title = parse_german_amount(title)
                            
                            bucket = BucketList.objects.get(id=list_id)
                            item = ListItem.objects.create(
                                bucket_list=bucket, 
                                title=parsed_title,
                                amount=parsed_amount,
                                shop=parsed_shop,
                                price=parsed_price,
                                guest_created_by="Alexa",
                                guest_updated_by="Alexa"
                            )
                            
                            # Construct beautiful detailed speech response
                            details = []
                            if parsed_amount:
                                details.append(parsed_amount)
                            details.append(parsed_title)
                            if parsed_shop:
                                details.append(f"von {parsed_shop}")
                            if parsed_price:
                                details.append(f"für {parsed_price:.2f} Euro".replace('.', ','))
                                
                            response_text = f"Ich habe {' '.join(details)} auf deine Liste {bucket.title} gesetzt."
                        except BucketList.DoesNotExist:
                            response_text = "Ich konnte deine Liste leider nicht finden. Bitte prüfe die Listen ID."
                    else:
                        response_text = "Ich habe den Namen des Elements leider nicht verstanden. Bitte versuche es noch einmal."
                        
                    return alexa_json({
                        'version': '1.0',
                        'response': {
                            'outputSpeech': {
                                'type': 'PlainText',
                                'text': response_text
                            },
                            'shouldEndSession': True
                        }
                    })
                
                # Help or Stop intent
                elif intent_name in ['AMAZON.HelpIntent', 'AMAZON.NavigateHomeIntent', 'AMAZON.FallbackIntent']:
                    return alexa_json({
                        'version': '1.0',
                        'response': {
                            'outputSpeech': {
                                'type': 'PlainText',
                                'text': "Das habe ich leider nicht verstanden. Sage zum Beispiel: setze Mehl auf die Einkaufsliste."
                            },
                            'reprompt': {
                                'outputSpeech': {
                                    'type': 'PlainText',
                                    'text': "Was soll ich auf die Einkaufsliste setzen?"
                                }
                            },
                            'shouldEndSession': False
                        }
                    })
                elif intent_name in ['AMAZON.CancelIntent', 'AMAZON.StopIntent']:
                    return alexa_json({
                        'version': '1.0',
                        'response': {
                            'outputSpeech': {
                                'type': 'PlainText',
                                'text': "Tschüss!"
                            },
                            'shouldEndSession': True
                        }
                    })
            
            # SessionEndedRequest
            return alexa_json({
                'version': '1.0',
                'response': {
                    'shouldEndSession': True
                }
            })
            
        except Exception as e:
            return alexa_json({
                'version': '1.0',
                'response': {
                    'outputSpeech': {
                        'type': 'PlainText',
                        'text': "Es gab leider einen Fehler bei der Verbindung zu Buckezz."
                    },
                    'shouldEndSession': True
                }
            })

class ICalExportView(View):
    def get(self, request, pk):
        bucket = get_object_or_404(BucketList, id=pk)
        # Check access
        if not (bucket.owner == request.user or (request.user.is_authenticated and request.user in bucket.shared_with.all()) or bucket.is_public):
            return HttpResponseForbidden()
            
        items = bucket.items.filter(models.Q(start_date__isnull=False) | models.Q(end_date__isnull=False))
        
        lines = [
            'BEGIN:VCALENDAR',
            'VERSION:2.0',
            'PRODID:-//buckezz//NONSGML v1.0//EN',
            f'X-WR-CALNAME:{bucket.title}',
        ]
        
        for item in items:
            dt_start = item.start_date.strftime('%Y%m%d') if item.start_date else item.end_date.strftime('%Y%m%d')
            dt_end = item.end_date.strftime('%Y%m%d') if item.end_date else item.start_date.strftime('%Y%m%d')
            
            lines.extend([
                'BEGIN:VEVENT',
                f'UID:{item.id}@buckezz.app',
                f'DTSTAMP:{timezone.now().strftime("%Y%m%dT%H%M%SZ")}',
                f'DTSTART;VALUE=DATE:{dt_start}',
                f'DTEND;VALUE=DATE:{dt_end}',
                f'SUMMARY:{item.title}',
                f'DESCRIPTION:{item.notes}',
                'END:VEVENT'
            ])
            
        lines.append('END:VCALENDAR')
        
        response = HttpResponse('\r\n'.join(lines), content_type='text/calendar')
        response['Content-Disposition'] = f'attachment; filename="{bucket.title}.ics"'
        return response

class QuickAddPersonView(View):
    def post(self, request):
        name = request.POST.get('name')
        if not name:
            return JsonResponse({'error': 'Name is required'}, status=400)
        person = Person.objects.create(name=name)
        return JsonResponse({'id': person.id, 'name': person.name})

import datetime

class PersonalICalFeedView(View):
    def get(self, request, token):
        person = get_object_or_404(Person, access_token=token)
        user = person.user
        if not user:
            return HttpResponse("Kein Benutzer mit dieser Person verknüpft.", status=400, content_type="text/plain")

        # Die Heimat-Zeitzone des Benutzers für den iCal-Export aktivieren
        import zoneinfo
        from django.utils import timezone
        if hasattr(user, 'settings'):
            try:
                timezone.activate(zoneinfo.ZoneInfo(user.settings.timezone))
            except Exception:
                pass

        lists = BucketList.objects.filter(
            models.Q(owner=user) | models.Q(shared_with=user)
        ).distinct()

        items = ListItem.objects.filter(
            bucket_list__in=lists
        ).filter(
            models.Q(start_date__isnull=False) |
            models.Q(end_date__isnull=False) |
            models.Q(reminder_at__isnull=False)
        ).select_related('bucket_list', 'bucket_list__category')

        refresh_interval = user.settings.calendar_refresh_interval if hasattr(user, 'settings') else 'PT15M'

        lines = [
            'BEGIN:VCALENDAR',
            'VERSION:2.0',
            'PRODID:-//buckezz//Personal Calendar Feed//EN',
            f'X-WR-CALNAME:Buckezz - {person.name}',
            'CALSCALE:GREGORIAN',
            'METHOD:PUBLISH',
            f'X-PUBLISHED-TTL:{refresh_interval}',
            f'REFRESH-INTERVAL;VALUE=DURATION:{refresh_interval}',
        ]

        tz_name = user.settings.timezone if hasattr(user, 'settings') else 'Europe/Berlin'
        try:
            user_tz = zoneinfo.ZoneInfo(tz_name)
        except Exception:
            user_tz = zoneinfo.ZoneInfo('Europe/Berlin')

        def format_ical_local_date(dt):
            if not dt:
                return ""
            if timezone.is_aware(dt):
                local_dt = dt.astimezone(user_tz)
            else:
                try:
                    local_dt = timezone.make_aware(dt).astimezone(user_tz)
                except Exception:
                    local_dt = timezone.make_aware(dt, user_tz)
            return local_dt.strftime("%Y%m%dT%H%M%S")

        def get_item_dtstamp(item):
            dt = item.updated_at or item.created_at or timezone.now()
            if timezone.is_aware(dt):
                utc_dt = dt.astimezone(datetime.timezone.utc)
            else:
                utc_dt = timezone.make_aware(dt, datetime.timezone.utc)
            return utc_dt.strftime("%Y%m%dT%H%M%SZ")

        for item in items:
            cat_icon = item.bucket_list.category.icon if item.bucket_list.category else "📌"
            dtstamp = get_item_dtstamp(item)
            
            # 1. Date Range
            if item.start_date and item.end_date:
                lines.extend([
                    'BEGIN:VEVENT',
                    f'UID:buckezz-item-range-{item.id}@buckezz.app',
                    f'DTSTAMP:{dtstamp}',
                    f'DTSTART;TZID={tz_name}:{format_ical_local_date(item.start_date)}',
                    f'DTEND;TZID={tz_name}:{format_ical_local_date(item.end_date)}',
                    f'SUMMARY:{cat_icon} {item.title}',
                    f'DESCRIPTION:Liste: {item.bucket_list.title}\\n\\nNotizen:\\n{item.notes or ""}',
                    'END:VEVENT'
                ])
            else:
                # 2. Start Date only
                if item.start_date:
                    end_dt = item.start_date + datetime.timedelta(hours=1)
                    lines.extend([
                        'BEGIN:VEVENT',
                        f'UID:buckezz-item-start-{item.id}@buckezz.app',
                        f'DTSTAMP:{dtstamp}',
                        f'DTSTART;TZID={tz_name}:{format_ical_local_date(item.start_date)}',
                        f'DTEND;TZID={tz_name}:{format_ical_local_date(end_dt)}',
                        f'SUMMARY:{cat_icon} {item.title} (Start)',
                        f'DESCRIPTION:Liste: {item.bucket_list.title}\\n\\nNotizen:\\n{item.notes or ""}',
                        'END:VEVENT'
                    ])
                # 3. End Date only
                if item.end_date:
                    start_dt = item.end_date - datetime.timedelta(hours=1)
                    lines.extend([
                        'BEGIN:VEVENT',
                        f'UID:buckezz-item-end-{item.id}@buckezz.app',
                        f'DTSTAMP:{dtstamp}',
                        f'DTSTART;TZID={tz_name}:{format_ical_local_date(start_dt)}',
                        f'DTEND;TZID={tz_name}:{format_ical_local_date(item.end_date)}',
                        f'SUMMARY:🏁 {cat_icon} {item.title}',
                        f'DESCRIPTION:Liste: {item.bucket_list.title}\\n\\nNotizen:\\n{item.notes or ""}',
                        'END:VEVENT'
                    ])
            
            # 4. Reminder
            if item.reminder_at:
                end_dt = item.reminder_at + datetime.timedelta(minutes=30)
                lines.extend([
                    'BEGIN:VEVENT',
                    f'UID:buckezz-item-rem-{item.id}@buckezz.app',
                    f'DTSTAMP:{dtstamp}',
                    f'DTSTART;TZID={tz_name}:{format_ical_local_date(item.reminder_at)}',
                    f'DTEND;TZID={tz_name}:{format_ical_local_date(end_dt)}',
                    f'SUMMARY:⏰ {item.title} (Erinnerung)',
                    f'DESCRIPTION:Liste: {item.bucket_list.title}\\n\\nNotizen:\\n{item.notes or ""}',
                    'BEGIN:VALARM',
                    'ACTION:DISPLAY',
                    f'DESCRIPTION:Erinnerung: {item.title}',
                    'TRIGGER:-PT0M',  # Trigger alert exactly at the start time
                    'END:VALARM',
                    'END:VEVENT'
                ])

        lines.append('END:VCALENDAR')
        
        response = HttpResponse('\r\n'.join(lines), content_type='text/calendar')
        response['Content-Disposition'] = f'attachment; filename="buckezz_{person.name}_calendar.ics"'
        return response
