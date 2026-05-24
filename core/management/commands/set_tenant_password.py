from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from core.router import register_tenant_db
from core.models import Tenant, UserSetting, Person

class Command(BaseCommand):
    help = 'Erstellt oder aktualisiert einen Admin-Benutzer in einer spezifischen Mandanten-Datenbank.'

    def add_arguments(self, parser):
        parser.add_argument('tenant_slug', type=str, help='Subdomain/Slug des Mandanten')
        parser.add_argument('username', type=str, help='Benutzername')
        parser.add_argument('password', type=str, help='Neues Passwort')

    def handle(self, *args, **options):
        tenant_slug = options['tenant_slug'].strip().lower()
        username = options['username'].strip()
        password = options['password']

        # 1. Prüfen, ob der Mandant existiert
        tenant = Tenant.objects.using('default').filter(slug=tenant_slug).first()
        if not tenant:
            self.stderr.write(self.style.ERROR(f"❌ Mandant '{tenant_slug}' existiert nicht in der Zentral-Datenbank!"))
            return

        db_alias = register_tenant_db(tenant_slug)

        # 2. Suchen oder Erstellen des Users
        user = User.objects.using(db_alias).filter(username=username).first()
        if user:
            user.set_password(password)
            user.is_superuser = True
            user.is_staff = True
            user.save(using=db_alias)
            self.stdout.write(self.style.SUCCESS(f"✅ Passwort für bestehenden Admin '{username}' in Mandant '{tenant_slug}' wurde aktualisiert!"))
        else:
            user = User.objects.db_manager(db_alias).create_superuser(
                username=username,
                email=tenant.owner_email or f"{username}@{tenant_slug}.local",
                password=password
            )
            UserSetting.objects.using(db_alias).get_or_create(user=user)
            Person.objects.using(db_alias).get_or_create(
                name=username,
                defaults={'email': user.email, 'user': user}
            )
            self.stdout.write(self.style.SUCCESS(f"🎉 Neuer Admin-Benutzer '{username}' wurde in Mandant '{tenant_slug}' erfolgreich angelegt!"))
