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
    readonly_fields = ('template_creation_guide',)
    fields = ('template_creation_guide', 'name', 'slug', 'icon')

    def template_creation_guide(self, obj):
        from django.utils.safestring import mark_safe
        return mark_safe("""
            <div style="background: #1e1e1e; color: #e0e0e0; padding: 22px; border-radius: 8px; border: 1px solid #3c3c3c; line-height: 1.6; font-size: 13px; max-width: 850px; margin-bottom: 20px; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;">
                <h3 style="color: #00adb5; margin-top: 0; font-size: 16px; border-bottom: 1px solid #3c3c3c; padding-bottom: 10px; display: flex; align-items: center; gap: 8px; font-weight: 600;">
                    ℹ️ Premium-Leitfaden für Listen-Vorlagen (Admins)
                </h3>
                <p style="margin: 0 0 16px 0; color: #a0a0a0;">Willkommen in der Vorlagen-Verwaltung! Wenn du eine neue Vorlage (Kategorie) erstellst, bestimmst du das Verhalten und die verfügbaren Felder der Liste. Folge diesem Leitfaden:</p>
                
                <h4 style="color: #ff8a5c; margin: 16px 0 8px 0; font-size: 14px; font-weight: 600;">1. Workflow & Logik-Typ (logic_type) bestimmen:</h4>
                <p style="margin: 0 0 10px 0;">Wähle unter <strong>Logik-Typ</strong> die passende Verhaltensweise für die Liste aus. Das verändert den gesamten Workflow:</p>
                <ul style="padding-left: 20px; margin: 0 0 16px 0; list-style-type: square; color: #ccc;">
                    <li style="margin-bottom: 6px;"><strong>Allgemein (generic):</strong> Klassischer Listen-Workflow. Elemente können als erledigt abgehakt werden.</li>
                    <li style="margin-bottom: 6px;"><strong>To-Do Liste (todo):</strong> Optimiert für Aufgaben mit Personen-Zuweisung und automatischen Mail-Erinnerungen.</li>
                    <li style="margin-bottom: 6px;"><strong>Geschenkeliste (gift):</strong> Aktiviert das <strong>Reservierungs- & Wichtelsystem</strong>. Schenkende können Wünsche reservieren (🔒) oder erfüllen (🎁). Der Empfänger der Geschenke (Beschenkte/owner) sieht diese Zuordnungen und Statusänderungen nicht (Überraschungs-Schutz!), während alle anderen Schenkenden sie sehen, um Doppelkäufe zu vermeiden.</li>
                    <li style="margin-bottom: 6px;"><strong>Bucketliste (bucket):</strong> Für Lebensziele. Ermöglicht Zuordnung zu Lebensabschnitten (Milestones), Prioritäten-Sternen und eine editierbare "Erreicht-am"-Chronik nach dem Abhaken.</li>
                    <li style="margin-bottom: 6px;"><strong>Veranstaltungsplaner (event):</strong> Ermöglicht Budget- und Kostenkalkulation, Zuordnung von Aufgaben an Personen und exakte Zeiteinteilungen.</li>
                    <li style="margin-bottom: 6px;"><strong>Tracker / Gewohnheiten (tracker):</strong> Schaltet den Live-Tracker frei, über den Aktionen live und zeitgenau protokolliert werden (z.B. Medikamenteneinnahme, Gießen, Tierfütterung).</li>
                </ul>

                <h4 style="color: #ff8a5c; margin: 16px 0 8px 0; font-size: 14px; font-weight: 600;">2. Aktive Felder steuern:</h4>
                <p style="margin: 0 0 10px 0;">Aktiviere durch Anhaken nur die Felder, die für diese Liste wirklich Sinn machen. Das hält die Benutzeroberfläche für deine User extrem schlank:</p>
                <ul style="padding-left: 20px; margin: 0 0 16px 0; list-style-type: square; color: #ccc;">
                    <li style="margin-bottom: 6px;"><strong>Menge (use_amount):</strong> Für Stückzahlen oder Dosen (z.B. Einkäufe, Weinflaschen, Medikamente).</li>
                    <li style="margin-bottom: 6px;"><strong>Marke (use_brand):</strong> Zeigt ein Marken- oder Herstellernamen-Feld an (wird bei Ärzten für den Arzt-/Praxisnamen verwendet).</li>
                    <li style="margin-bottom: 6px;"><strong>Geschäft (use_shop):</strong> Zeigt an, in welchem Geschäft (oder auf welcher Website) etwas besorgt werden soll.</li>
                    <li style="margin-bottom: 6px;"><strong>Preis (use_price):</strong> Schaltet die Preiserfassung frei. Bei Einkäufen/Events wird automatisch die Summe aller offenen Posten und die Gesamtsumme berechnet!</li>
                    <li style="margin-bottom: 6px;"><strong>Ort (use_location):</strong> Für Adressen, GPS-Orte oder Web-Links (z.B. Arztpraxis, Event-Ort, Wunschzettel-Shoplink).</li>
                    <li style="margin-bottom: 6px;"><strong>Startdatum (use_start_date) & Enddatum (use_end_date):</strong> Für zeitlich begrenzte Termine oder Einnahmephasen.</li>
                    <li style="margin-bottom: 6px;"><strong>Erinnerung (use_reminder):</strong> Schaltet E-Mail-Erinnerungen frei, die sich vollautomatisch an die lokale Zeitzone anpassen.</li>
                    <li style="margin-bottom: 6px;"><strong>Personen (use_persons):</strong> Für Zuständigkeiten, Wichtel-Teilnehmer oder Beteiligte.</li>
                    <li style="margin-bottom: 6px;"><strong>Tracker (use_tracker):</strong> Aktiviert das minutengenaue Live-Abhaken für regelmäßige Routinen.</li>
                </ul>

                <h4 style="color: #ff8a5c; margin: 16px 0 8px 0; font-size: 14px; font-weight: 600;">3. Hilfetexte schreiben:</h4>
                <p style="margin: 0;">Gib gute Hilfestellungen. Schreibe das <strong>Praxis-Beispiel</strong> sauber untereinander (mit normalen Zeilenumbrüchen). Das System rendert sie wunderschön zeilenweise im Browser-Info-Modal!</p>
            </div>
        """)
    template_creation_guide.short_description = "Premium Ausfüll-Hilfe & Anleitung"

# Customizing the Admin site titles and back link
admin.site.site_header = "Buckezz Administration"
admin.site.site_title = "Buckezz Admin"
admin.site.index_title = "Willkommen in der Buckezz Verwaltung"
admin.site.site_url = "/dashboard/"


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
