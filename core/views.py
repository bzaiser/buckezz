from django.db import models
from django.views.generic import TemplateView, ListView, DetailView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, render, redirect
from django.http import HttpResponse, HttpResponseForbidden
from django.core.exceptions import PermissionDenied
from .models import BucketList, ListItem, ListCategory, UserSetting, Person

class HomeView(TemplateView):
    template_name = 'core/home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        if user.is_authenticated:
            context['my_lists'] = BucketList.objects.filter(owner=user)
            allowed_lists = BucketList.objects.filter(
                models.Q(owner=user) | models.Q(shared_with=user) | models.Q(is_public=True)
            ).distinct()
        else:
            allowed_lists = BucketList.objects.filter(is_public=True)
            
        context['categories'] = ListCategory.objects.prefetch_related(
            models.Prefetch('lists', queryset=allowed_lists, to_attr='visible_lists')
        )
        return context

class DashboardView(LoginRequiredMixin, ListView):
    model = BucketList
    template_name = 'core/dashboard.html'
    context_object_name = 'lists'

    def get_queryset(self):
        return BucketList.objects.filter(owner=self.request.user)
    
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

class BucketListDetailView(DetailView):
    model = BucketList
    template_name = 'core/list_detail.html'
    context_object_name = 'bucket'

    def get_queryset(self):
        # Allow owner, shared users OR public lists
        return BucketList.objects.all()

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        # Check permissions
        is_owner = obj.owner == self.request.user
        is_shared = self.request.user.is_authenticated and self.request.user in obj.shared_with.all()
        if not (is_owner or is_shared or obj.is_public):
            raise PermissionDenied("Zugriff verweigert.")
        return obj

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        if not request.user.is_authenticated and not request.session.get('guest_name'):
            return render(request, 'core/guest_login.html', {'bucket': self.object})
        context = self.get_context_data(object=self.object)
        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        guest_name = request.POST.get('guest_name')
        if guest_name:
            request.session['guest_name'] = guest_name.strip()
        return redirect('core:list_detail', pk=self.kwargs['pk'])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        bucket = self.get_object()
        # Check if user can edit
        can_edit = bucket.owner == self.request.user or \
                  (self.request.user.is_authenticated and self.request.user in bucket.shared_with.all()) or \
                  (bucket.is_public and bucket.allow_public_edit)
        context['can_edit'] = can_edit
        
        items = bucket.items.all()
        context['active_items'] = [i for i in items if not i.is_completed]
        context['completed_items'] = [i for i in items if i.is_completed]
        
        return context

def render_item_list(request, bucket, can_edit):
    items = bucket.items.all()
    active_items = [i for i in items if not i.is_completed]
    completed_items = [i for i in items if i.is_completed]
    return render(request, 'core/partials/item_list.html', {
        'bucket': bucket,
        'active_items': active_items,
        'completed_items': completed_items,
        'can_edit': can_edit
    })

class GetItemFormView(View):
    def get(self, request, bucket_id, item_id=None):
        bucket = get_object_or_404(BucketList, id=bucket_id)
        # Permission check
        can_edit = bucket.owner == request.user or \
                  (request.user.is_authenticated and request.user in bucket.shared_with.all()) or \
                  (bucket.is_public and bucket.allow_public_edit)
        if not can_edit:
            return HttpResponseForbidden()
            
        item = None
        if item_id:
            item = get_object_or_404(ListItem, id=item_id)
        
        people = Person.objects.all()
        return render(request, 'core/partials/item_form.html', {'bucket': bucket, 'item': item, 'people': people})

class AddItemView(View):
    def post(self, request, bucket_id):
        bucket = get_object_or_404(BucketList, id=bucket_id)
        can_edit = bucket.owner == request.user or \
                  (request.user.is_authenticated and request.user in bucket.shared_with.all()) or \
                  (bucket.is_public and bucket.allow_public_edit)
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
            start_date=data.get('start_date') if data.get('start_date') else None,
            end_date=data.get('end_date') if data.get('end_date') else None,
            notes=data.get('notes'),
            created_by=request.user if request.user.is_authenticated else None,
            guest_created_by=guest_name if not request.user.is_authenticated else None
        )
        
        # Handle persons
        person_ids = request.POST.getlist('persons')
        if person_ids:
            item.involved_persons.set(person_ids)
        
        if request.htmx:
            return render_item_list(request, bucket, True)
        return HttpResponse(status=204)

class EditItemView(View):
    def post(self, request, item_id):
        item = get_object_or_404(ListItem, id=item_id)
        bucket = item.bucket_list
        can_edit = bucket.owner == request.user or \
                  (request.user.is_authenticated and request.user in bucket.shared_with.all()) or \
                  (bucket.is_public and bucket.allow_public_edit)
        if not can_edit:
            return HttpResponseForbidden()

        data = request.POST
        item.title = data.get('title')
        item.amount = data.get('amount')
        item.price = data.get('price') if data.get('price') else None
        item.brand = data.get('brand')
        item.shop = data.get('shop')
        item.location = data.get('location')
        item.start_date = data.get('start_date') if data.get('start_date') else None
        item.end_date = data.get('end_date') if data.get('end_date') else None
        item.notes = data.get('notes')
        
        if request.user.is_authenticated:
            item.updated_by = request.user
            item.guest_updated_by = None
        else:
            item.updated_by = None
            item.guest_updated_by = request.session.get('guest_name')
            
        item.save()
        
        # Handle persons
        person_ids = request.POST.getlist('persons')
        if person_ids:
            item.involved_persons.set(person_ids)
        else:
            item.involved_persons.clear()
        
        if request.htmx:
            return render_item_list(request, bucket, True)
        return HttpResponse(status=204)

class ToggleItemView(View):
    def post(self, request, pk):
        item = get_object_or_404(ListItem, pk=pk)
        bucket = item.bucket_list
        can_edit = bucket.owner == request.user or \
                  (request.user.is_authenticated and request.user in bucket.shared_with.all()) or \
                  (bucket.is_public and bucket.allow_public_edit)
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
        item = get_object_or_404(ListItem, pk=pk)
        bucket = item.bucket_list
        if bucket.owner != request.user and not (bucket.is_public and bucket.allow_public_edit):
            return HttpResponseForbidden()
            
        item.delete()
        if request.htmx:
            return render_item_list(request, bucket, True)
        return HttpResponse("")

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
            
        bucket.save()
        return render(request, 'core/partials/share_controls.html', {'bucket': bucket})

class ThemeSettingsView(LoginRequiredMixin, View):
    def get(self, request):
        settings, _ = UserSetting.objects.get_or_create(user=request.user)
        return render(request, 'core/settings.html', {'settings': settings})

    def post(self, request):
        settings, _ = UserSetting.objects.get_or_create(user=request.user)
        settings.primary_color = request.POST.get('primary_color')
        settings.accent_color = request.POST.get('accent_color')
        settings.bg_color = request.POST.get('bg_color')
        settings.text_color = request.POST.get('text_color')
        settings.input_bg_color = request.POST.get('input_bg_color', '#000000')
        settings.input_text_color = request.POST.get('input_text_color', '#ffffff')
        settings.glass_opacity = request.POST.get('glass_opacity')
        settings.save()
        return redirect('core:dashboard')
