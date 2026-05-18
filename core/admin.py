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
