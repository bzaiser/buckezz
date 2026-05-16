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
    glass_opacity = models.DecimalField(max_digits=3, decimal_places=2, default=0.15)

    def __str__(self):
        return f"Settings for {self.user.username}"

class Person(models.Model):
    name = models.CharField(max_length=255)
    email = models.EmailField(blank=True, null=True)
    user = models.OneToOneField(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='person_profile')

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
    use_status = models.BooleanField(default=True)

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
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = _("Liste")
        verbose_name_plural = _("Listen")

class ListItem(models.Model):
    bucket_list = models.ForeignKey(BucketList, on_delete=models.CASCADE, related_name='items')
    title = models.CharField(max_length=255)
    
    # Potential fields (managed by template)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    amount = models.CharField(max_length=100, null=True, blank=True)
    brand = models.CharField(max_length=255, null=True, blank=True)
    shop = models.CharField(max_length=255, null=True, blank=True)
    
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
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
    
    involved_persons = models.ManyToManyField(Person, related_name='items', blank=True)
    notes = models.TextField(blank=True)
    
    is_completed = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_items')
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='updated_items')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['order', '-created_at']
        verbose_name = _("Listen-Eintrag")
        verbose_name_plural = _("Listen-Einträge")
