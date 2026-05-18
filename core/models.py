from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _
import uuid

class UserSetting(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='settings')
    primary_color = models.CharField(max_length=7, default='#00d2ff')
    accent_color = models.CharField(max_length=7, default='#ffab00')
    bg_color = models.CharField(max_length=7, default='#0a0e14')
    text_color = models.CharField(max_length=7, default='#ffffff')
    input_bg_color = models.CharField(max_length=7, default='#000000')
    input_text_color = models.CharField(max_length=7, default='#ffffff')
    glass_opacity = models.DecimalField(max_digits=3, decimal_places=2, default=0.15)

    def __str__(self):
        return f"Settings for {self.user.username}"

class Person(models.Model):
    name = models.CharField(max_length=255)
    email = models.EmailField(blank=True, null=True)
    user = models.OneToOneField(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='person_profile')
    access_token = models.UUIDField(default=uuid.uuid4, unique=True)
    birth_date = models.DateField(null=True, blank=True)

    @property
    def age(self):
        if not self.birth_date:
            return None
        from django.utils import timezone
        today = timezone.localdate()
        return today.year - self.birth_date.year - ((today.month, today.day) < (self.birth_date.month, self.birth_date.day))

    @property
    def active_milestone(self):
        current_age = self.age
        if current_age is None:
            return None
        if current_age < 30:
            return 'before_30'
        elif current_age < 40:
            return 'before_40'
        elif current_age < 50:
            return 'before_50'
        elif current_age < 60:
            return 'before_60'
        else:
            return 'before_die'

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _("Person")
        verbose_name_plural = _("Personen")

class ListCategory(models.Model):
    name = models.CharField(max_length=100)
    icon = models.CharField(max_length=50, help_text="Lucide-Icon Name oder Emoji", default="📋")
    slug = models.SlugField(unique=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _("Listen-Kategorie")
        verbose_name_plural = _("Listen-Kategorien")

class ListTemplate(models.Model):
    category = models.OneToOneField(ListCategory, on_delete=models.CASCADE, related_name='template')
    
    # Configuration which fields are active
    use_price = models.BooleanField(default=False)
    use_amount = models.BooleanField(default=False)
    use_brand = models.BooleanField(default=False)
    use_shop = models.BooleanField(default=False)
    use_start_date = models.BooleanField(default=False)
    use_end_date = models.BooleanField(default=False)
    use_reminder = models.BooleanField(default=False)
    use_location = models.BooleanField(default=False)
    use_persons = models.BooleanField(default=False)
    use_url = models.BooleanField(default=False)
    use_status = models.BooleanField(default=True)
    use_rating = models.BooleanField(default=False)
    use_tracker = models.BooleanField(default=False)
    use_milestone = models.BooleanField(default=False)

    # Customizable help guidelines
    help_purpose = models.TextField(blank=True, null=True, help_text="💡 Zweck der Vorlage (z.B. Ideal für den Wocheneinkauf)")
    help_fields = models.TextField(blank=True, null=True, help_text="🛠️ Welche Felder aktiv sind und wie man sie nutzt")
    help_example = models.TextField(blank=True, null=True, help_text="📝 Praxis-Beispiel für einen Eintrag")

    def __str__(self):
        return f"Template für {self.category.name}"

class BucketList(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    category = models.ForeignKey(ListCategory, on_delete=models.PROTECT, related_name='lists')
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='owned_lists')
    shared_with = models.ManyToManyField(User, related_name='shared_lists', blank=True)
    is_public = models.BooleanField(default=False, help_text="Zugriff über Link ohne Login möglich")
    allow_public_edit = models.BooleanField(default=False, help_text="Personen mit Link dürfen Einträge hinzufügen/ändern")
    
    beneficiary = models.ForeignKey(Person, on_delete=models.SET_NULL, null=True, blank=True, related_name='beneficiary_lists', help_text="Für wen ist diese Liste? (z.B. Geburtstagskind)")
    is_secret_santa = models.BooleanField(default=False, help_text="Versteckt Zuordnungen vor dem Begünstigten")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    @property
    def beneficiary_person(self):
        if self.beneficiary:
            return self.beneficiary
        # Find if the owner user has a Person profile
        from core.models import Person
        return Person.objects.filter(user=self.owner).first()

    class Meta:
        verbose_name = _("Liste")
        verbose_name_plural = _("Listen")

class ListParticipant(models.Model):
    bucket_list = models.ForeignKey(BucketList, on_delete=models.CASCADE, related_name='participants')
    person = models.ForeignKey(Person, on_delete=models.CASCADE, related_name='participating_in')
    link_sent = models.BooleanField(default=False)

    class Meta:
        unique_together = ('bucket_list', 'person')
        verbose_name = _("Listen-Teilnehmer")
        verbose_name_plural = _("Listen-Teilnehmer")

class ListItem(models.Model):
    bucket_list = models.ForeignKey(BucketList, on_delete=models.CASCADE, related_name='items')
    title = models.CharField(max_length=255)
    
    # Potential fields (managed by template)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    amount = models.CharField(max_length=100, null=True, blank=True)
    brand = models.CharField(max_length=255, null=True, blank=True)
    shop = models.CharField(max_length=255, null=True, blank=True)
    url = models.URLField(max_length=1000, null=True, blank=True)
    rating = models.PositiveSmallIntegerField(null=True, blank=True)
    
    tracker_unit = models.CharField(max_length=100, null=True, blank=True, help_text=_("Einheit, z.B. Tablette, Portion, ml"))
    tracker_times = models.CharField(max_length=255, null=True, blank=True, help_text=_("Komma-separierte Uhrzeiten, z.B. 08:00, 18:00"))
    tracker_stock_total = models.IntegerField(null=True, blank=True, help_text=_("Aktueller Gesamtbestand im Kasten/Packung"))
    tracker_stock_min = models.IntegerField(null=True, blank=True, help_text=_("Warnschwelle für Nachbestellung"))
    tracker_dosage_per_take = models.FloatField(default=1.0, help_text=_("Verbrauch pro Abhaken"))
    
    start_date = models.DateTimeField(null=True, blank=True)
    end_date = models.DateTimeField(null=True, blank=True)
    reminder_at = models.DateTimeField(null=True, blank=True)
    reminder_sent = models.BooleanField(default=False)
    
    location = models.CharField(max_length=255, null=True, blank=True)
    
    STATUS_CHOICES = [
        ('active', _('Aktiv')),
        ('done', _('Erledigt')),
        ('overdue', _('Überfällig')),
        ('waiting', _('Wartend')),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    
    MILESTONE_CHOICES = [
        ('before_30', _('Vor 30')),
        ('before_40', _('Vor 40')),
        ('before_50', _('Vor 50')),
        ('before_60', _('Vor 60')),
        ('before_die', _('Bevor ich sterbe')),
    ]
    target_milestone = models.CharField(max_length=20, choices=MILESTONE_CHOICES, null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    @property
    def age_at_completion(self):
        beneficiary = self.bucket_list.beneficiary_person
        if not self.completed_at or not beneficiary or not beneficiary.birth_date:
            return None
        birth = beneficiary.birth_date
        comp = self.completed_at.date()
        return comp.year - birth.year - ((comp.month, comp.day) < (birth.month, birth.day))
    
    involved_persons = models.ManyToManyField(Person, through='ItemPersonRole', related_name='items', blank=True)
    notes = models.TextField(blank=True)
    
    is_completed = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_items')
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='updated_items')
    guest_created_by = models.CharField(max_length=100, blank=True, null=True)
    guest_updated_by = models.CharField(max_length=100, blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if self.is_completed:
            if not self.completed_at:
                from django.utils import timezone
                self.completed_at = timezone.now()
        else:
            self.completed_at = None
        super().save(*args, **kwargs)

    @property
    def completed_tracker_times_today(self):
        from django.utils import timezone
        today = timezone.localdate()
        return list(self.tracker_logs.filter(date=today).values_list('scheduled_time', flat=True))

    @property
    def tracker_times_list(self):
        if not self.tracker_times:
            return []
        return [t.strip() for t in self.tracker_times.split(',') if t.strip()]

    class Meta:
        ordering = ['order', '-created_at']
        verbose_name = _("Listen-Eintrag")
        verbose_name_plural = _("Listen-Einträge")

class ItemPersonRole(models.Model):
    STATUS_CHOICES = [
        ('assigned', _('Zuständig')),
        ('invited', _('Eingeladen')),
        ('attending', _('Zugesagt')),
        ('declined', _('Abgesagt')),
        ('maybe', _('Vielleicht')),
        ('reserved', _('Reserviert')),
        ('fulfilled', _('Wunsch erfüllt'))
    ]
    item = models.ForeignKey(ListItem, on_delete=models.CASCADE, related_name='person_roles')
    person = models.ForeignKey(Person, on_delete=models.CASCADE, related_name='item_roles')
    role = models.CharField(max_length=20, choices=STATUS_CHOICES, default='assigned')

    class Meta:
        unique_together = ('item', 'person')
        verbose_name = _("Personen-Zuordnung")
        verbose_name_plural = _("Personen-Zuordnungen")

class ItemTrackerLog(models.Model):
    item = models.ForeignKey(ListItem, on_delete=models.CASCADE, related_name='tracker_logs')
    date = models.DateField(auto_now_add=True)
    scheduled_time = models.CharField(max_length=5) # z.B. "08:00"
    completed = models.BooleanField(default=True)
    completed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('item', 'date', 'scheduled_time')
        verbose_name = _("Tracker-Protokoll")
        verbose_name_plural = _("Tracker-Protokolle")

    def __str__(self):
        return f"{self.item.title} am {self.date} um {self.scheduled_time}"
