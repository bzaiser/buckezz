from django.db import models
from django.views.generic import View
from django.shortcuts import get_object_or_404
from django.http import JsonResponse, HttpResponse, HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from .models import BucketList, ListItem, Person
import environ
from django.utils import timezone

env = environ.Env()

@method_decorator(csrf_exempt, name='dispatch')
class AlexaAddItemView(View):
    def post(self, request):
        token = request.headers.get('Authorization') or request.POST.get('token')
        if token != env('ALEXA_TOKEN', default='secret-alexa-token'):
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

        lines = [
            'BEGIN:VCALENDAR',
            'VERSION:2.0',
            'PRODID:-//buckezz//Personal Calendar Feed//EN',
            f'X-WR-CALNAME:Buckezz - {person.name}',
            'CALSCALE:GREGORIAN',
            'METHOD:PUBLISH'
        ]

        def format_ical_date(dt):
            if not dt:
                return ""
            utc_dt = dt.astimezone(timezone.utc) if timezone.is_active(dt) else dt
            return utc_dt.strftime("%Y%m%dT%H%M%SZ")

        now_str = timezone.now().strftime("%Y%m%dT%H%M%SZ")

        for item in items:
            cat_icon = item.bucket_list.category.icon if item.bucket_list.category else "📌"
            
            # 1. Date Range
            if item.start_date and item.end_date:
                lines.extend([
                    'BEGIN:VEVENT',
                    f'UID:buckezz-item-range-{item.id}@buckezz.app',
                    f'DTSTAMP:{now_str}',
                    f'DTSTART:{format_ical_date(item.start_date)}',
                    f'DTEND:{format_ical_date(item.end_date)}',
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
                        f'DTSTAMP:{now_str}',
                        f'DTSTART:{format_ical_date(item.start_date)}',
                        f'DTEND:{format_ical_date(end_dt)}',
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
                        f'DTSTAMP:{now_str}',
                        f'DTSTART:{format_ical_date(start_dt)}',
                        f'DTEND:{format_ical_date(item.end_date)}',
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
                    f'DTSTAMP:{now_str}',
                    f'DTSTART:{format_ical_date(item.reminder_at)}',
                    f'DTEND:{format_ical_date(end_dt)}',
                    f'SUMMARY:⏰ {item.title} (Erinnerung)',
                    f'DESCRIPTION:Liste: {item.bucket_list.title}\\n\\nNotizen:\\n{item.notes or ""}',
                    'END:VEVENT'
                ])

        lines.append('END:VCALENDAR')
        
        response = HttpResponse('\r\n'.join(lines), content_type='text/calendar')
        response['Content-Disposition'] = f'attachment; filename="buckezz_{person.name}_calendar.ics"'
        return response
