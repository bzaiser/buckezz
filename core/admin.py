from django.contrib import admin
from .models import Person, ListCategory, ListTemplate, BucketList, ListItem, ItemPersonRole, ListParticipant, ItemTrackerLog

class ListTemplateInline(admin.StackedInline):
    model = ListTemplate
    can_delete = False

@admin.register(ListCategory)
class ListCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'icon')
    prepopulated_fields = {'slug': ('name',)}
    inlines = [ListTemplateInline]

from .models import UserSetting

@admin.register(UserSetting)
class UserSettingAdmin(admin.ModelAdmin):
    list_display = ('user', 'primary_color', 'bg_color')
    search_fields = ('user__username',)

@admin.register(Person)
class PersonAdmin(admin.ModelAdmin):
    list_display = ('name', 'birth_date', 'email', 'user', 'access_token')
    search_fields = ('name', 'email')

class ListItemInline(admin.TabularInline):
    model = ListItem
    extra = 1

class ListParticipantInline(admin.TabularInline):
    model = ListParticipant
    extra = 1

@admin.register(BucketList)
class BucketListAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'owner', 'created_at', 'is_secret_santa', 'beneficiary')
    list_filter = ('category', 'owner', 'is_secret_santa')
    search_fields = ('title',)
    inlines = [ListItemInline, ListParticipantInline]
    actions = ['duplicate_bucket_lists']

    @admin.action(description="Ausgewählte Listen duplizieren (Kopieren)")
    def duplicate_bucket_lists(self, request, queryset):
        from core.models import ListParticipant, ListItem, ItemPersonRole
        
        count = 0
        for old_bucket in queryset:
            # 1. Duplicate BucketList
            new_bucket = BucketList.objects.create(
                title=f"{old_bucket.title} (Kopie)",
                category=old_bucket.category,
                owner=old_bucket.owner,
                is_public=old_bucket.is_public,
                allow_public_edit=old_bucket.allow_public_edit,
                beneficiary=old_bucket.beneficiary,
                is_secret_santa=old_bucket.is_secret_santa
            )
            
            # 2. Copy shared_with
            new_bucket.shared_with.set(old_bucket.shared_with.all())
            
            # 3. Copy ListParticipant
            for part in old_bucket.participants.all():
                ListParticipant.objects.create(
                    bucket_list=new_bucket,
                    person=part.person,
                    link_sent=part.link_sent
                )
                
            # 4. Copy ListItem
            for item in old_bucket.items.all():
                new_item = ListItem.objects.create(
                    bucket_list=new_bucket,
                    title=item.title,
                    price=item.price,
                    amount=item.amount,
                    brand=item.brand,
                    shop=item.shop,
                    url=item.url,
                    rating=item.rating,
                    tracker_unit=item.tracker_unit,
                    tracker_times=item.tracker_times,
                    tracker_stock_total=item.tracker_stock_total,
                    tracker_stock_min=item.tracker_stock_min,
                    tracker_dosage_per_take=item.tracker_dosage_per_take,
                    start_date=item.start_date,
                    end_date=item.end_date,
                    reminder_at=item.reminder_at,
                    reminder_sent=False,
                    location=item.location,
                    status='active',
                    target_milestone=item.target_milestone,
                    notes=item.notes,
                    is_completed=False,
                    order=item.order,
                    created_by=item.created_by
                )
                # Copy involved persons (ItemPersonRole):
                for role_entry in item.person_roles.all():
                    ItemPersonRole.objects.create(
                        item=new_item,
                        person=role_entry.person,
                        role=role_entry.role
                    )
            count += 1
            
        self.message_user(request, f"{count} Liste(n) wurde(n) erfolgreich dupliziert (Einträge zurückgesetzt).")

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(owner=request.user)

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.owner = request.user
        super().save_model(request, obj, form, change)

@admin.register(ItemPersonRole)
class ItemPersonRoleAdmin(admin.ModelAdmin):
    list_display = ('item', 'person', 'role')
    list_filter = ('role', 'person')


@admin.register(ListItem)
class ListItemAdmin(admin.ModelAdmin):
    list_display = ('title', 'bucket_list', 'status', 'is_completed', 'target_milestone', 'completed_at')
    list_filter = ('status', 'is_completed', 'bucket_list', 'target_milestone')
    search_fields = ('title', 'notes')

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(bucket_list__owner=request.user)

@admin.register(ListParticipant)
class ListParticipantAdmin(admin.ModelAdmin):
    list_display = ('bucket_list', 'person', 'link_sent')
    list_filter = ('link_sent', 'bucket_list')

@admin.register(ItemTrackerLog)
class ItemTrackerLogAdmin(admin.ModelAdmin):
    list_display = ('item', 'date', 'scheduled_time', 'completed', 'completed_at')
    list_filter = ('date', 'scheduled_time', 'completed')
