from django.contrib import admin
from .models import Person, ListCategory, ListTemplate, BucketList, ListItem

class ListTemplateInline(admin.StackedInline):
    model = ListTemplate
    can_delete = False

@admin.register(ListCategory)
class ListCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'icon')
    prepopulated_fields = {'slug': ('name',)}
    inlines = [ListTemplateInline]

@admin.register(Person)
class PersonAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'user')
    search_fields = ('name', 'email')

class ListItemInline(admin.TabularInline):
    model = ListItem
    extra = 1

@admin.register(BucketList)
class BucketListAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'owner', 'created_at')
    list_filter = ('category', 'owner')
    search_fields = ('title',)
    inlines = [ListItemInline]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(owner=request.user)

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.owner = request.user
        super().save_model(request, obj, form, change)

@admin.register(ListItem)
class ListItemAdmin(admin.ModelAdmin):
    list_display = ('title', 'bucket_list', 'status', 'is_completed')
    list_filter = ('status', 'is_completed', 'bucket_list')
    search_fields = ('title', 'notes')

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(bucket_list__owner=request.user)
