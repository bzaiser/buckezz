from django.db import models
from django.views.generic import TemplateView, ListView, DetailView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, render, redirect
from django.http import HttpResponse, HttpResponseForbidden
from django.core.exceptions import PermissionDenied
from .models import BucketList, ListItem, ListCategory, UserSetting, Person, ItemPersonRole, ListParticipant

class HomeView(TemplateView):
    template_name = 'core/home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        person_id = self.request.session.get('person_id')
        
        if user.is_authenticated:
            if user.is_superuser:
                context['my_lists'] = BucketList.objects.all()
                allowed_lists = BucketList.objects.all()
            else:
                context['my_lists'] = BucketList.objects.filter(owner=user)
                allowed_lists = BucketList.objects.filter(
                    models.Q(owner=user) | models.Q(shared_with=user) | models.Q(participants__person__user=user)
                ).distinct()
        elif person_id:
            allowed_lists = BucketList.objects.filter(
                participants__person_id=person_id
            ).distinct()
        else:
            allowed_lists = BucketList.objects.none()
            
        context['categories'] = ListCategory.objects.prefetch_related(
            models.Prefetch('lists', queryset=allowed_lists, to_attr='visible_lists')
        )
        return context

class DashboardView(LoginRequiredMixin, ListView):
    model = BucketList
    template_name = 'core/dashboard.html'
    context_object_name = 'lists'

    def get_queryset(self):
        if self.request.user.is_superuser:
            return BucketList.objects.all()
        return BucketList.objects.filter(
            models.Q(owner=self.request.user) | models.Q(shared_with=self.request.user)
        ).distinct()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = ListCategory.objects.all()
        return context

class CreateBucketView(LoginRequiredMixin, View):
    def post(self, request):
        category_id = request.POST.get('category_id')
        title = request.POST.get('title')
        
        if not category_id or not title:
            return redirect('core:dashboard')
            
        category = get_object_or_404(ListCategory, id=category_id)
        bucket = BucketList.objects.create(
            owner=request.user,
            category=category,
            title=title
        )
        return redirect('core:list_detail', pk=bucket.id)

def get_list_items_for_user(request, bucket):
    # Get current person from session or user profile
    current_person = None
    person_id = request.session.get('person_id')
    if person_id:
        try:
            current_person = Person.objects.get(id=person_id)
        except Person.DoesNotExist:
            pass
    elif request.user.is_authenticated:
        try:
            current_person = request.user.person_profile
        except Person.DoesNotExist:
            pass
            
    is_beneficiary = False
    if bucket.is_secret_santa and bucket.beneficiary and current_person == bucket.beneficiary:
        is_beneficiary = True

    items = bucket.items.all()
    
    # Live Search Filter
    q = request.GET.get('q')
    if q:
        items = items.filter(title__icontains=q.strip())
        
    if is_beneficiary:
        # Beneficiary sees all items as active (hiding completed/fulfilled ones)
        active_items = list(items)
        completed_items = []
    else:
        active_items = [i for i in items if not i.is_completed]
        completed_items = [i for i in items if i.is_completed]
        
    return active_items, completed_items, is_beneficiary, current_person

def group_items_by_milestone(active_items, completed_items, beneficiary):
    milestones_cfg = [
        ('before_30', 'Vor 30'),
        ('before_40', 'Vor 40'),
        ('before_50', 'Vor 50'),
        ('before_60', 'Vor 60'),
        ('before_die', 'Bevor ich sterbe'),
        ('', 'Ohne Meilenstein')
    ]
    
    active_focus = beneficiary.active_milestone if beneficiary else None
    
    grouped_active = []
    for slug, label in milestones_cfg:
        m_items = [i for i in active_items if (i.target_milestone or '') == slug]
        if m_items:
            grouped_active.append({
                'slug': slug,
                'label': label,
                'items': m_items,
                'is_current': slug == active_focus
            })
            
    grouped_completed = []
    for slug, label in milestones_cfg:
        m_items = [i for i in completed_items if (i.target_milestone or '') == slug]
        if m_items:
            grouped_completed.append({
                'slug': slug,
                'label': label,
                'items': m_items
            })
            
    if active_focus:
        milestone_order = ['before_30', 'before_40', 'before_50', 'before_60', 'before_die', '']
        try:
            focus_idx = milestone_order.index(active_focus)
        except ValueError:
            focus_idx = 0
            
        def sort_weight(group):
            slug = group['slug']
            if slug == active_focus:
                return 0
            if not slug:
                return 100
            try:
                idx = milestone_order.index(slug)
            except ValueError:
                idx = 99
            if idx > focus_idx:
                return idx
            else:
                return 50 + idx
                
        grouped_active.sort(key=sort_weight)
        
    return grouped_active, grouped_completed, active_focus

class BucketListDetailView(DetailView):
    template_name = 'core/list_detail.html'
    context_object_name = 'bucket'

    def get_queryset(self):
        return BucketList.objects.all()

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        # Check permissions
        is_owner = obj.owner == self.request.user
        is_shared = self.request.user.is_authenticated and self.request.user in obj.shared_with.all()
        is_admin = self.request.user.is_authenticated and self.request.user.is_superuser
        
        # If public or is_secret_santa (which works with personalized links) or superuser/admin
        if not (is_owner or is_shared or obj.is_public or obj.is_secret_santa or is_admin):
            raise PermissionDenied("Zugriff verweigert.")
        return obj

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        
        # Personalized token auto-login
        token_str = request.GET.get('p')
        if token_str:
            try:
                person = Person.objects.get(access_token=token_str)
                request.session['person_id'] = person.id
                request.session['guest_name'] = person.name
            except (Person.DoesNotExist, ValueError):
                pass
                
        # Access control for Secret Santa lists
        if self.object.is_secret_santa:
            is_owner = self.object.owner == request.user
            person_id = request.session.get('person_id')
            
            # Auto-associate logged in user's person profile
            if request.user.is_authenticated and not person_id:
                try:
                    person = request.user.person_profile
                    request.session['person_id'] = person.id
                    request.session['guest_name'] = person.name
                except Person.DoesNotExist:
                    pass
                    
            if not is_owner and not request.session.get('person_id'):
                return render(request, 'core/secret_santa_error.html', {'bucket': self.object})
        elif not request.user.is_authenticated and not request.session.get('guest_name'):
            return render(request, 'core/guest_login.html', {'bucket': self.object})
            
        # Trigger Edeka Microsoft To-Do real-time sync (throttled to once every 10 seconds per session)
        if self.object.todo_sync_url and self.object.category.template.logic_type == 'todo':
            import time
            session_key = f'last_todo_sync_{self.object.id}'
            last_sync = request.session.get(session_key, 0)
            now = time.time()
            if now - last_sync > 10:
                sync_microsoft_todo(self.object)
                request.session[session_key] = now

        context = self.get_context_data(object=self.object)
        if request.headers.get('HX-Request') == 'true' and 'q' in request.GET:
            return render(request, 'core/partials/item_list.html', context)
        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        guest_name = request.POST.get('guest_name')
        if guest_name:
            request.session['guest_name'] = guest_name.strip()
        return redirect('core:list_detail', pk=self.kwargs['pk'])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        bucket = self.get_object()
        
        active_items, completed_items, is_beneficiary, current_person = get_list_items_for_user(self.request, bucket)
        
        grouped_active = None
        grouped_completed = None
        if bucket.category.template.use_milestone:
            beneficiary = bucket.beneficiary_person
            grouped_active, grouped_completed, _ = group_items_by_milestone(active_items, completed_items, beneficiary)
        
        is_owner = bucket.owner == self.request.user
        is_admin = self.request.user.is_authenticated and self.request.user.is_superuser
        if bucket.is_secret_santa:
            can_edit = is_owner or is_beneficiary or is_admin
        else:
            can_edit = is_owner or is_admin or \
                      (self.request.user.is_authenticated and self.request.user in bucket.shared_with.all()) or \
                      (bucket.is_public and bucket.allow_public_edit)
                      
        context['can_edit'] = can_edit
        context['active_items'] = active_items
        context['completed_items'] = completed_items
        context['grouped_active'] = grouped_active
        context['grouped_completed'] = grouped_completed
        context['is_beneficiary'] = is_beneficiary
        context['current_person'] = current_person
        context['people'] = Person.objects.all()
        
        # Inject workout specific details
        if bucket.category.template.logic_type == 'workout':
            sessions_qs = bucket.workout_sessions.all().prefetch_related('activities')
            context['workout_sessions'] = sessions_qs
            
            import json
            from django.core.serializers.json import DjangoJSONEncoder
            sessions_data = []
            for session in reversed(sessions_qs):
                session_dict = {
                    'id': session.id,
                    'date': session.date.strftime('%d.%m.%Y'),
                    'isoDate': session.date.strftime('%Y-%m-%d'),
                    'duration_minutes': round(session.duration_seconds / 60),
                    'rating': session.rating,
                    'notes': session.notes,
                    'activities': []
                }
                for act in session.activities.all():
                    session_dict['activities'].append({
                        'title': act.title,
                        'type': act.activity_type,
                        'data': act.logged_data_json
                    })
                sessions_data.append(session_dict)
            context['workout_sessions_json'] = json.dumps(sessions_data, cls=DjangoJSONEncoder)
            
            if self.request.user.is_authenticated:
                from core.models import UserSetting
                user_settings, _ = UserSetting.objects.get_or_create(user=self.request.user)
                context['user_settings'] = user_settings
        
        return context

def render_item_list(request, bucket, can_edit):
    active_items, completed_items, is_beneficiary, current_person = get_list_items_for_user(request, bucket)
    
    grouped_active = None
    grouped_completed = None
    if bucket.category.template.use_milestone:
        beneficiary = bucket.beneficiary_person
        grouped_active, grouped_completed, _ = group_items_by_milestone(active_items, completed_items, beneficiary)
        
    is_owner = bucket.owner == request.user
    if bucket.is_secret_santa:
        can_edit = is_owner or is_beneficiary
    else:
        can_edit = is_owner or \
                  (request.user.is_authenticated and request.user in bucket.shared_with.all()) or \
                  (bucket.is_public and bucket.allow_public_edit)
                  
    return render(request, 'core/partials/item_list.html', {
        'bucket': bucket,
        'active_items': active_items,
        'completed_items': completed_items,
        'grouped_active': grouped_active,
        'grouped_completed': grouped_completed,
        'can_edit': can_edit,
        'is_beneficiary': is_beneficiary,
        'current_person': current_person
    })

class GetItemFormView(View):
    def get(self, request, bucket_id, item_id=None):
        bucket = get_object_or_404(BucketList, id=bucket_id)
        
        # 1. View Permission Check
        is_owner = bucket.owner == request.user
        is_shared = request.user.is_authenticated and request.user in bucket.shared_with.all()
        is_admin = request.user.is_authenticated and request.user.is_superuser
        
        # Secret Santa session checks
        person_id = request.session.get('person_id')
        current_person = None
        if person_id:
            try:
                current_person = Person.objects.get(id=person_id)
            except Person.DoesNotExist:
                pass
        
        is_beneficiary = False
        if bucket.is_secret_santa and bucket.beneficiary and current_person == bucket.beneficiary:
            is_beneficiary = True

        can_view = is_owner or is_shared or bucket.is_public or (bucket.is_secret_santa and (is_owner or person_id)) or is_admin
        if not can_view:
            return HttpResponseForbidden("Zugriff verweigert.")
            
        # 2. Edit Permission Check
        if bucket.is_secret_santa:
            can_edit = is_owner or is_beneficiary or is_admin
        else:
            can_edit = is_owner or is_shared or (bucket.is_public and bucket.allow_public_edit) or is_admin
            
        item = None
        gift_status = "open"
        gift_person = None
        if item_id:
            item = get_object_or_404(ListItem, id=item_id)
            gift_role = item.person_roles.filter(role__in=['reserved', 'fulfilled']).first()
            if gift_role:
                gift_status = gift_role.role
                gift_person = gift_role.person
        
        people = Person.objects.all()
        return render(request, 'core/partials/item_form.html', {
            'bucket': bucket,
            'item': item,
            'people': people,
            'can_edit': can_edit,
            'is_beneficiary': is_beneficiary,
            'current_person': current_person,
            'gift_status': gift_status,
            'gift_person': gift_person
        })

class AddItemView(View):
    def post(self, request, bucket_id):
        bucket = get_object_or_404(BucketList, id=bucket_id)
        can_edit = bucket.owner == request.user or \
                  (request.user.is_authenticated and request.user in bucket.shared_with.all()) or \
                  (bucket.is_public and bucket.allow_public_edit) or \
                  (request.user.is_authenticated and request.user.is_superuser)
        if not can_edit:
            return HttpResponseForbidden()

        data = request.POST
        guest_name = request.session.get('guest_name')
        item = ListItem.objects.create(
            bucket_list=bucket,
            title=data.get('title'),
            amount=data.get('amount'),
            price=data.get('price') if data.get('price') else None,
            brand=data.get('brand'),
            shop=data.get('shop'),
            location=data.get('location'),
            url=data.get('url'),
            start_date=data.get('start_date') if data.get('start_date') else None,
            end_date=data.get('end_date') if data.get('end_date') else None,
            notes=data.get('notes'),
            target_milestone=data.get('target_milestone') if data.get('target_milestone') else None,
            rating=data.get('rating') if data.get('rating') else None,
            tracker_unit=data.get('tracker_unit'),
            tracker_times=data.get('tracker_times'),
            tracker_stock_total=int(data.get('tracker_stock_total')) if data.get('tracker_stock_total') else None,
            tracker_stock_min=int(data.get('tracker_stock_min')) if data.get('tracker_stock_min') else None,
            tracker_dosage_per_take=float(data.get('tracker_dosage_per_take')) if data.get('tracker_dosage_per_take') else 1.0,
            reminder_at=data.get('reminder_at') if data.get('reminder_at') else None,
            created_by=request.user if request.user.is_authenticated else None,
            guest_created_by=guest_name if not request.user.is_authenticated else None,
            workout_type=data.get('workout_type', 'strength')
        )
        
        # Save workout config
        workout_type = data.get('workout_type', 'strength')
        if workout_type == 'strength':
            try:
                sets_count = int(data.get('workout_sets_count') or 3)
            except ValueError:
                sets_count = 3
            try:
                rest_time = int(data.get('workout_rest_time') or 120)
            except ValueError:
                rest_time = 120
            item.workout_config_json = {
                'sets_count': sets_count,
                'target_reps': data.get('workout_target_reps', '').strip(),
                'target_weight': data.get('workout_target_weight', '').strip(),
                'rest_time': rest_time
            }
        elif workout_type == 'endurance':
            item.workout_config_json = {
                'target_distance': data.get('workout_target_distance', '').strip(),
                'target_duration': data.get('workout_target_duration', '').strip(),
                'target_pace': data.get('workout_target_pace', '').strip(),
            }
        elif workout_type == 'interval':
            item.workout_config_json = {
                'interval_format': data.get('workout_interval_format', 'AMRAP').strip(),
                'interval_duration': data.get('workout_interval_duration', '').strip(),
            }
        item.save()
        
        # Handle persons
        person_ids = request.POST.getlist('persons')
        if person_ids:
            for pid in person_ids:
                ItemPersonRole.objects.create(item=item, person_id=pid)
        
        # Handle custom status box
        item_status = request.POST.get('item_status')
        if item_status:
            # Find current person
            person_id = request.session.get('person_id')
            current_person = None
            if person_id:
                try:
                    current_person = Person.objects.get(id=person_id)
                except Person.DoesNotExist:
                    pass
            if not current_person and request.user.is_authenticated:
                current_person = Person.objects.filter(user=request.user).first()

            if bucket.category.template.logic_type == 'gift':
                if item_status == 'open':
                    item.person_roles.filter(role__in=['reserved', 'fulfilled']).delete()
                    item.is_completed = False
                elif item_status in ['reserved', 'fulfilled'] and current_person:
                    item.person_roles.filter(role__in=['reserved', 'fulfilled']).delete()
                    role, _ = ItemPersonRole.objects.get_or_create(item=item, person=current_person)
                    role.role = item_status
                    role.save()
                    item.is_completed = (item_status == 'fulfilled')
            else:
                if item_status == 'completed':
                    item.is_completed = True
                    item.status = 'done'
                elif item_status == 'open':
                    item.is_completed = False
                    item.status = 'active'
            item.save()
        
        if request.htmx:
            return render_item_list(request, bucket, True)
        return HttpResponse(status=204)
 
class EditItemView(View):
    def post(self, request, item_id):
        item = get_object_or_404(ListItem, id=item_id)
        bucket = item.bucket_list
        can_edit = bucket.owner == request.user or \
                  (request.user.is_authenticated and request.user in bucket.shared_with.all()) or \
                  (bucket.is_public and bucket.allow_public_edit) or \
                  (request.user.is_authenticated and request.user.is_superuser)
        if not can_edit:
            return HttpResponseForbidden()
 
        data = request.POST
        item.title = data.get('title')
        item.amount = data.get('amount')
        item.price = data.get('price') if data.get('price') else None
        item.brand = data.get('brand')
        item.shop = data.get('shop')
        item.location = data.get('location')
        item.url = data.get('url')
        item.start_date = data.get('start_date') if data.get('start_date') else None
        item.end_date = data.get('end_date') if data.get('end_date') else None
        item.notes = data.get('notes')
        item.target_milestone = data.get('target_milestone') if data.get('target_milestone') else None
        item.rating = data.get('rating') if data.get('rating') else None
        
        # Retroactive completion date override for milestone lists
        if item.is_completed and bucket.category.template.use_milestone:
            completed_at_val = data.get('completed_at')
            if completed_at_val:
                from django.utils.dateparse import parse_datetime
                from django.utils import timezone
                parsed = parse_datetime(completed_at_val)
                if parsed:
                    if timezone.is_naive(parsed):
                        parsed = timezone.make_aware(parsed)
                    item.completed_at = parsed
        item.tracker_unit = data.get('tracker_unit')
        item.tracker_times = data.get('tracker_times')
        item.tracker_stock_total = int(data.get('tracker_stock_total')) if data.get('tracker_stock_total') else None
        item.tracker_stock_min = int(data.get('tracker_stock_min')) if data.get('tracker_stock_min') else None
        item.tracker_dosage_per_take = float(data.get('tracker_dosage_per_take')) if data.get('tracker_dosage_per_take') else 1.0
        item.reminder_at = data.get('reminder_at') if data.get('reminder_at') else None
        
        # Save workout config
        workout_type = data.get('workout_type', 'strength')
        item.workout_type = workout_type
        if workout_type == 'strength':
            try:
                sets_count = int(data.get('workout_sets_count') or 3)
            except ValueError:
                sets_count = 3
            try:
                rest_time = int(data.get('workout_rest_time') or 120)
            except ValueError:
                rest_time = 120
            item.workout_config_json = {
                'sets_count': sets_count,
                'target_reps': data.get('workout_target_reps', '').strip(),
                'target_weight': data.get('workout_target_weight', '').strip(),
                'rest_time': rest_time
            }
        elif workout_type == 'endurance':
            item.workout_config_json = {
                'target_distance': data.get('workout_target_distance', '').strip(),
                'target_duration': data.get('workout_target_duration', '').strip(),
                'target_pace': data.get('workout_target_pace', '').strip(),
            }
        elif workout_type == 'interval':
            item.workout_config_json = {
                'interval_format': data.get('workout_interval_format', 'AMRAP').strip(),
                'interval_duration': data.get('workout_interval_duration', '').strip(),
            }
        
        if request.user.is_authenticated:
            item.updated_by = request.user
            item.guest_updated_by = None
        else:
            item.updated_by = None
            item.guest_updated_by = request.session.get('guest_name')
            
        item.save()
        
        # Handle persons
        person_ids = request.POST.getlist('persons')
        new_pids = set(int(p) for p in person_ids)
        current_pids = set(item.person_roles.values_list('person_id', flat=True))
        
        # Remove persons not in the new list (except reserved/fulfilled roles which are status-tracked)
        ItemPersonRole.objects.filter(item=item, person_id__in=current_pids - new_pids).exclude(role__in=['reserved', 'fulfilled']).delete()
        
        # Add new persons
        for pid in new_pids - current_pids:
            ItemPersonRole.objects.create(item=item, person_id=pid)
            
        # Handle custom status box
        item_status = request.POST.get('item_status')
        if item_status:
            # Find current person
            person_id = request.session.get('person_id')
            current_person = None
            if person_id:
                try:
                    current_person = Person.objects.get(id=person_id)
                except Person.DoesNotExist:
                    pass
            if not current_person and request.user.is_authenticated:
                current_person = Person.objects.filter(user=request.user).first()

            if bucket.category.template.logic_type == 'gift':
                if item_status == 'open':
                    item.person_roles.filter(role__in=['reserved', 'fulfilled']).delete()
                    item.is_completed = False
                elif item_status in ['reserved', 'fulfilled'] and current_person:
                    item.person_roles.filter(role__in=['reserved', 'fulfilled']).delete()
                    role, _ = ItemPersonRole.objects.get_or_create(item=item, person=current_person)
                    role.role = item_status
                    role.save()
                    item.is_completed = (item_status == 'fulfilled')
            else:
                if item_status == 'completed':
                    item.is_completed = True
                    item.status = 'done'
                elif item_status == 'open':
                    item.is_completed = False
                    item.status = 'active'
            item.save()
        
        if request.htmx:
            return render_item_list(request, bucket, True)
        return HttpResponse(status=204)

class ToggleItemView(View):
    def post(self, request, pk):
        item = get_object_or_404(ListItem, pk=pk)
        bucket = item.bucket_list
        can_edit = bucket.owner == request.user or \
                  (request.user.is_authenticated and request.user in bucket.shared_with.all()) or \
                  (bucket.is_public and bucket.allow_public_edit) or \
                  (request.user.is_authenticated and request.user.is_superuser)
        if not can_edit:
            return HttpResponseForbidden()
        
        item.is_completed = not item.is_completed
        item.status = 'done' if item.is_completed else 'active'
        
        if request.user.is_authenticated:
            item.updated_by = request.user
            item.guest_updated_by = None
        else:
            item.updated_by = None
            item.guest_updated_by = request.session.get('guest_name')
            
        item.save()
        
        if request.htmx:
            return render_item_list(request, bucket, True)
        return HttpResponse(status=204)

class DeleteItemView(View):
    def delete(self, request, pk):
        return self._do_delete(request, pk)

    def post(self, request, pk):
        return self._do_delete(request, pk)

    def _do_delete(self, request, pk):
        item = get_object_or_404(ListItem, pk=pk)
        bucket = item.bucket_list
        is_owner = bucket.owner == request.user
        is_admin = request.user.is_authenticated and request.user.is_superuser
        is_public_editable = bucket.is_public and bucket.allow_public_edit
        if not (is_owner or is_admin or is_public_editable):
            return HttpResponseForbidden()

        item.delete()
        if request.htmx:
            return render_item_list(request, bucket, True)
        return HttpResponse("")

    def post(self, request, pk):
        return self.delete(request, pk)


class ReorderItemsView(LoginRequiredMixin, View):
    def post(self, request, bucket_id):
        import json
        bucket = get_object_or_404(BucketList, id=bucket_id)
        is_owner = bucket.owner == request.user
        is_admin = request.user.is_authenticated and request.user.is_superuser
        if not (is_owner or is_admin):
            return HttpResponseForbidden()
        try:
            data = json.loads(request.body)
            order = data.get('order', [])  # list of item IDs in new order
            for idx, item_id in enumerate(order):
                ListItem.objects.filter(pk=item_id, bucket_list=bucket).update(order=idx)
            return JsonResponse({'status': 'ok'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

class ShareToggleView(LoginRequiredMixin, View):
    def post(self, request, pk):
        bucket = get_object_or_404(BucketList, id=pk)
        if bucket.owner != request.user:
            return HttpResponseForbidden()
        
        action = request.POST.get('action')
        if action == 'toggle_public':
            bucket.is_public = not bucket.is_public
            # If we disable public access, also disable public edit for safety
            if not bucket.is_public:
                bucket.allow_public_edit = False
        elif action == 'toggle_edit':
            bucket.allow_public_edit = not bucket.allow_public_edit
        elif action == 'toggle_secret_santa':
            bucket.is_secret_santa = not bucket.is_secret_santa
        elif action == 'set_beneficiary':
            beneficiary_id = request.POST.get('beneficiary_id')
            if beneficiary_id:
                bucket.beneficiary_id = beneficiary_id
            else:
                bucket.beneficiary = None
        elif action == 'set_todo_sync_url':
            todo_sync_url = request.POST.get('todo_sync_url', '').strip()
            bucket.todo_sync_url = todo_sync_url if todo_sync_url else None
        elif action == 'add_participant':
            person_id = request.POST.get('person_id')
            new_person_name = request.POST.get('new_person_name')
            if person_id:
                person = get_object_or_404(Person, id=person_id)
                ListParticipant.objects.get_or_create(bucket_list=bucket, person=person)
            elif new_person_name:
                person = Person.objects.create(name=new_person_name.strip())
                ListParticipant.objects.create(bucket_list=bucket, person=person)
        elif action == 'remove_participant':
            participant_id = request.POST.get('participant_id')
            if participant_id:
                participant = get_object_or_404(ListParticipant, id=participant_id, bucket_list=bucket)
                participant.delete()
        elif action == 'toggle_participant_sent':
            participant_id = request.POST.get('participant_id')
            if participant_id:
                participant = get_object_or_404(ListParticipant, id=participant_id, bucket_list=bucket)
                participant.link_sent = not participant.link_sent
                participant.save()
            
        bucket.save()
        people = Person.objects.all()
        return render(request, 'core/partials/share_controls.html', {
            'bucket': bucket,
            'people': people
        })

class CyclePersonRoleView(View):
    def post(self, request, role_id):
        role = get_object_or_404(ItemPersonRole, id=role_id)
        bucket = role.item.bucket_list
        
        current_person_id = request.session.get('person_id')
        is_own_role = current_person_id and role.person_id == current_person_id
        
        can_edit = bucket.owner == request.user or \
                  (request.user.is_authenticated and request.user in bucket.shared_with.all()) or \
                  (bucket.is_public and bucket.allow_public_edit) or \
                  (bucket.is_secret_santa and is_own_role)
                  
        if not can_edit:
            return HttpResponseForbidden()
            
        if bucket.is_secret_santa:
            if role.role == 'reserved':
                role.role = 'fulfilled'
                role.save()
                role.item.is_completed = True
                role.item.save()
            else:
                role.delete()
                other_fulfilled = role.item.person_roles.filter(role='fulfilled').exclude(id=role.id).exists()
                if not other_fulfilled:
                    role.item.is_completed = False
                    role.item.save()
        else:
            new_role = request.POST.get('role')
            if new_role and new_role in [c[0] for c in ItemPersonRole.STATUS_CHOICES]:
                role.role = new_role
                role.save()
            else:
                choices = [c[0] for c in ItemPersonRole.STATUS_CHOICES]
                current_index = choices.index(role.role)
                next_index = (current_index + 1) % len(choices)
                role.role = choices[next_index]
                role.save()
            
            # If the role is now 'fulfilled', mark the list item completed
            if role.role == 'fulfilled':
                role.item.is_completed = True
                role.item.save()
            else:
                # If it transitioned away from fulfilled, make sure it's marked active
                # (only if no other person role is currently 'fulfilled' on this item)
                other_fulfilled = role.item.person_roles.filter(role='fulfilled').exclude(id=role.id).exists()
                if not other_fulfilled:
                    role.item.is_completed = False
                    role.item.save()
        
        if request.htmx:
            return render_item_list(request, bucket, True)
        return HttpResponse(status=204)

class ToggleReservationView(View):
    def post(self, request, item_id):
        item = get_object_or_404(ListItem, id=item_id)
        bucket = item.bucket_list
        
        person_id = request.session.get('person_id')
        if not person_id and request.user.is_authenticated:
            try:
                person = request.user.person_profile
                person_id = person.id
            except Person.DoesNotExist:
                pass
                
        if not person_id:
            return HttpResponseForbidden("Kein Teilnehmer-Profil gefunden.")
            
        person = get_object_or_404(Person, id=person_id)
        
        # Toggle the reservation:
        role, created = ItemPersonRole.objects.get_or_create(item=item, person=person)
        if not created:
            if role.role == 'reserved':
                role.role = 'fulfilled'
                role.save()
                item.is_completed = True
                item.save()
            else:
                role.delete()
                item.is_completed = False
                item.save()
        else:
            role.role = 'reserved'
            role.save()
            
        if request.htmx:
            return render_item_list(request, bucket, True)
        return HttpResponse(status=204)

class ThemeSettingsView(LoginRequiredMixin, View):
    def get(self, request):
        settings, _ = UserSetting.objects.get_or_create(user=request.user)
        from core.models import Person
        person, _ = Person.objects.get_or_create(user=request.user, defaults={'name': request.user.username})
        return render(request, 'core/settings.html', {'settings': settings, 'person': person})

    def post(self, request):
        settings, _ = UserSetting.objects.get_or_create(user=request.user)
        settings.primary_color = request.POST.get('primary_color')
        settings.accent_color = request.POST.get('accent_color')
        settings.bg_color = request.POST.get('bg_color')
        settings.text_color = request.POST.get('text_color')
        settings.input_bg_color = request.POST.get('input_bg_color', '#000000')
        settings.input_text_color = request.POST.get('input_text_color', '#ffffff')
        settings.glass_opacity = request.POST.get('glass_opacity')
        settings.timezone = request.POST.get('timezone', 'Europe/Berlin')
        
        try:
            settings.calendar_start_hour = int(request.POST.get('calendar_start_hour', 8))
        except (ValueError, TypeError):
            settings.calendar_start_hour = 8
            
        try:
            settings.calendar_end_hour = int(request.POST.get('calendar_end_hour', 22))
        except (ValueError, TypeError):
            settings.calendar_end_hour = 22
            
        settings.calendar_filter_tracker = request.POST.get('calendar_filter_tracker') == 'on'
        settings.calendar_filter_reminder = request.POST.get('calendar_filter_reminder') == 'on'
        settings.calendar_filter_completed = request.POST.get('calendar_filter_completed') == 'on'
        settings.calendar_refresh_interval = request.POST.get('calendar_refresh_interval', 'PT15M')
        
        # Save Gym & Workout settings
        gym_weight = request.POST.get('gym_weight')
        if gym_weight:
            try:
                settings.gym_weight = float(gym_weight)
            except ValueError:
                pass
        else:
            settings.gym_weight = None
            
        settings.gym_fitness_goal = request.POST.get('gym_fitness_goal', '').strip()
        settings.gym_nutrition_plan_url = request.POST.get('gym_nutrition_plan_url', '').strip() or None
        
        try:
            settings.gym_plan_adaptation_weeks = int(request.POST.get('gym_plan_adaptation_weeks', 4))
        except (ValueError, TypeError):
            settings.gym_plan_adaptation_weeks = 4
            
        settings.gym_plan_adaptation_message = request.POST.get('gym_plan_adaptation_message', '').strip()
        
        # Save measurements
        measurements = {
            'brust': request.POST.get('measure_brust', '').strip(),
            'ruecken': request.POST.get('measure_ruecken', '').strip(),
            'arm_l': request.POST.get('measure_arm_l', '').strip(),
            'arm_r': request.POST.get('measure_arm_r', '').strip(),
            'bauch': request.POST.get('measure_bauch', '').strip(),
            'bein_l': request.POST.get('measure_bein_l', '').strip(),
            'bein_r': request.POST.get('measure_bein_r', '').strip(),
        }
        settings.gym_body_measurements_json = measurements
        
        settings.save()
        
        # Save birth date
        birth_date = request.POST.get('birth_date')
        from core.models import Person
        person, _ = Person.objects.get_or_create(user=request.user, defaults={'name': request.user.username})
        if birth_date:
            person.birth_date = birth_date
        else:
            person.birth_date = None
        person.save()
        
        return redirect('core:dashboard')

from django.http import JsonResponse
class WorkoutLogSessionView(View):
    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'status': 'error', 'message': 'Nicht autorisiert'}, status=403)
        try:
            import json
            from core.models import WorkoutSessionLog, WorkoutActivityLog, BucketList
            data = json.loads(request.body)
            bucket_id = data.get('bucket_id')
            bucket = BucketList.objects.get(id=bucket_id)
            
            # Check permissions
            if bucket.owner != request.user and request.user not in bucket.shared_with.all():
                return JsonResponse({'status': 'error', 'message': 'Zugriff verweigert'}, status=403)
            
            session = WorkoutSessionLog.objects.create(
                user=request.user,
                bucket_list=bucket,
                duration_seconds=data.get('duration_seconds', 0),
                rating=data.get('rating', 5),
                notes=data.get('notes', '')
            )
            
            activities = data.get('activities', [])
            for act in activities:
                WorkoutActivityLog.objects.create(
                    session=session,
                    title=act.get('title'),
                    activity_type=act.get('activity_type', 'strength'),
                    logged_data_json=act.get('logged_data')
                )
                
            # Reset the list items for next training session
            bucket.items.all().update(is_completed=False, status='active', completed_at=None)
            
            return JsonResponse({'status': 'success', 'session_id': session.id})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

class DeleteWorkoutSessionView(LoginRequiredMixin, View):
    def post(self, request, session_id):
        from core.models import WorkoutSessionLog
        session = get_object_or_404(WorkoutSessionLog, id=session_id)
        if session.bucket_list.owner != request.user:
            return HttpResponseForbidden()
        session.delete()
        return JsonResponse({'status': 'ok'})

class ToggleTrackerLogView(View):
    def post(self, request, item_id):
        item = get_object_or_404(ListItem, id=item_id)
        bucket = item.bucket_list
        can_edit = bucket.owner == request.user or \
                  (request.user.is_authenticated and request.user in bucket.shared_with.all()) or \
                  (bucket.is_public and bucket.allow_public_edit) or \
                  (request.session.get('person_id') is not None) or \
                  (request.user.is_authenticated and request.user.is_superuser)
        if not can_edit:
            return HttpResponseForbidden()

        scheduled_time = request.POST.get('scheduled_time')
        if not scheduled_time:
            return HttpResponse(status=400)

        # Get today's date in local timezone
        from django.utils import timezone
        today = timezone.localdate()

        # Check if already completed
        from core.models import ItemTrackerLog
        log = ItemTrackerLog.objects.filter(item=item, date=today, scheduled_time=scheduled_time).first()

        if log:
            # Toggle off: delete log, restore inventory
            log.delete()
            if item.tracker_stock_total is not None:
                item.tracker_stock_total += int(item.tracker_dosage_per_take)
                item.save()
        else:
            # Toggle on: create log, subtract from inventory
            ItemTrackerLog.objects.create(item=item, scheduled_time=scheduled_time)
            if item.tracker_stock_total is not None:
                item.tracker_stock_total = max(0, item.tracker_stock_total - int(item.tracker_dosage_per_take))
                item.save()

        if request.htmx:
            return render_item_list(request, bucket, True)
        return HttpResponse(status=204)


from django.urls import reverse
import json

class CalendarView(LoginRequiredMixin, TemplateView):
    template_name = 'core/calendar.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get or lazily create Person profile for secure calendar feed token
        from core.models import Person
        person = Person.objects.filter(user=self.request.user).first()
        if not person and self.request.user.is_authenticated:
            person = Person.objects.create(
                user=self.request.user,
                name=self.request.user.get_full_name() or self.request.user.username,
                email=self.request.user.email
            )
        context['person'] = person

        # Fetch all lists where user is owner or shared_with
        if self.request.user.is_superuser:
            lists = BucketList.objects.all()
        else:
            lists = BucketList.objects.filter(
                models.Q(owner=self.request.user) | models.Q(shared_with=self.request.user)
            ).distinct()

        # Fetch all items with dates or tracker times from these lists
        items = ListItem.objects.filter(
            bucket_list__in=lists
        ).filter(
            models.Q(start_date__isnull=False) |
            models.Q(end_date__isnull=False) |
            models.Q(reminder_at__isnull=False) |
            (models.Q(tracker_times__isnull=False) & ~models.Q(tracker_times=''))
        ).select_related('bucket_list', 'bucket_list__category')

        events = []
        for item in items:
            list_url = reverse('core:list_detail', args=[item.bucket_list.id])
            cat_icon = item.bucket_list.category.icon if item.bucket_list.category else "📌"
            
            # Use distinct ids so FullCalendar doesn't complain about duplicates
            # 1. Start date & End date range
            if item.start_date and item.end_date:
                events.append({
                    'id': f"range-{item.id}",
                    'title': f"{cat_icon} {item.title}",
                    'start': item.start_date.isoformat(),
                    'end': item.end_date.isoformat(),
                    'allDay': False,
                    'url': list_url,
                    'color': 'var(--primary)',
                    'extendedProps': {
                        'listName': item.bucket_list.title,
                        'notes': item.notes,
                        'completed': item.is_completed
                    }
                })
            else:
                # 2. Only Start date
                if item.start_date:
                    events.append({
                        'id': f"start-{item.id}",
                        'title': f"{cat_icon} {item.title} (Start)",
                        'start': item.start_date.isoformat(),
                        'allDay': False,
                        'url': list_url,
                        'color': 'rgba(255,255,255,0.15)',
                        'extendedProps': {
                            'listName': item.bucket_list.title,
                            'notes': item.notes,
                            'completed': item.is_completed
                        }
                    })
                # 3. Only End date (due)
                if item.end_date:
                    events.append({
                        'id': f"end-{item.id}",
                        'title': f"🏁 {cat_icon} {item.title}",
                        'start': item.end_date.isoformat(),
                        'allDay': False,
                        'url': list_url,
                        'color': 'var(--accent)' if not item.is_completed else 'var(--primary)',
                        'extendedProps': {
                            'listName': item.bucket_list.title,
                            'notes': item.notes,
                            'completed': item.is_completed
                        }
                    })

            # 4. Reminder date and time
            if item.reminder_at:
                events.append({
                    'id': f"rem-{item.id}",
                    'title': f"⏰ {item.title} (Erinnerung)",
                    'start': item.reminder_at.isoformat(),
                    'allDay': False,
                    'url': list_url,
                    'color': '#ffab00',
                    'extendedProps': {
                        'listName': item.bucket_list.title,
                        'notes': item.notes,
                        'completed': item.is_completed
                    }
                })

            # 5. Recurring Daily Tracker Times
            if item.tracker_times:
                times_list = [t.strip() for t in item.tracker_times.split(',') if t.strip()]
                for t in times_list:
                    # Validate HH:MM format
                    if len(t) == 5 and t[2] == ':':
                        start_time = f"{t}:00"
                        try:
                            hour, minute = map(int, t.split(':'))
                            end_hour = hour
                            end_minute = minute + 30
                            if end_minute >= 60:
                                end_hour = (end_hour + 1) % 24
                                end_minute = end_minute - 60
                            end_time = f"{end_hour:02d}:{end_minute:02d}:00"
                        except Exception:
                            end_time = f"{t}:00"
                            
                        events.append({
                            'id': f"tracker-{item.id}-{t}",
                            'title': f"{cat_icon} {item.title}",
                            'startTime': start_time,
                            'endTime': end_time,
                            'daysOfWeek': [0, 1, 2, 3, 4, 5, 6], # Every day!
                            'url': list_url,
                            'color': 'rgba(0, 230, 118, 0.12)', # Soft neon-green glass
                            'borderColor': '#00e676',
                            'textColor': '#00e676',
                            'extendedProps': {
                                'listName': item.bucket_list.title,
                                'notes': f"Tägliche Routine um {t} Uhr.",
                                'completed': False
                            }
                        })

        context['events_json'] = json.dumps(events)
        return context


def sync_microsoft_todo(bucket_list):
    if not bucket_list.todo_sync_url:
        return
        
    import urllib.request
    import re
    from core.models import ListItem
    
    try:
        # Fetch the ICS content with a timeout of 3 seconds and a custom User-Agent
        req = urllib.request.Request(
            bucket_list.todo_sync_url, 
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Buckezz/1.0'}
        )
        with urllib.request.urlopen(req, timeout=3) as response:
            content = response.read().decode('utf-8')
            
        # Parse VTODO blocks in the ICS feed
        vtodo_blocks = re.findall(r'BEGIN:VTODO(.*?)END:VTODO', content, re.DOTALL)
        
        for block in vtodo_blocks:
            # Extract SUMMARY (the item text)
            summary_match = re.search(r'SUMMARY:(.*?)[\r\n]', block)
            status_match = re.search(r'STATUS:(.*?)[\r\n]', block)
            
            if summary_match:
                title = summary_match.group(1).strip()
                # Clean up standard ICS escapes (like \,)
                title = title.replace(r'\,', ',').replace(r'\;', ';')
                
                # Check status: uncompleted is NEEDS-ACTION
                status = status_match.group(1).strip() if status_match else 'NEEDS-ACTION'
                
                if status == 'NEEDS-ACTION':
                    # Only add if not already in the active list
                    if not ListItem.objects.filter(bucket_list=bucket_list, title=title, is_completed=False).exists():
                        ListItem.objects.create(
                            bucket_list=bucket_list,
                            title=title,
                            is_completed=False
                        )
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Microsoft To-Do sync failed for list {bucket_list.id}: {e}")

def custom_404_view(request, exception=None):
    from core.models import UserSetting
    # Try to load user settings for the theme
    user_settings = None
    if request.user.is_authenticated:
        user_settings, _ = UserSetting.objects.get_or_create(user=request.user)
    elif request.session.get('person_id'):
        from core.models import Person
        try:
            person = Person.objects.get(id=request.session.get('person_id'))
            if person.user:
                user_settings, _ = UserSetting.objects.get_or_create(user=person.user)
        except Person.DoesNotExist:
            pass

    return render(request, '404.html', {'user_settings': user_settings}, status=404)


