from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from core.models import BucketList, ListItem, ListCategory, ListTemplate, Person

class Command(BaseCommand):
    help = 'Creates the Buckezz-User group with appropriate permissions'

    def handle(self, *args, **options):
        group, created = Group.objects.get_or_create(name='Buckezz-User')
        
        # Permissions we want to grant
        permissions_to_add = []
        
        # Helper to add permissions by model and actions
        def add_perms(model, actions):
            ct = ContentType.objects.get_for_model(model)
            for action in actions:
                codename = f'{action}_{model._meta.model_name}'
                try:
                    perm = Permission.objects.get(content_type=ct, codename=codename)
                    permissions_to_add.append(perm)
                except Permission.DoesNotExist:
                    self.stdout.write(self.style.WARNING(f'Permission {codename} not found'))

        # Define permissions for each model
        add_perms(BucketList, ['add', 'change', 'view']) # No delete for safety
        add_perms(ListItem, ['add', 'change', 'delete', 'view'])
        add_perms(ListCategory, ['view']) # Categories are templates, user shouldn't change them
        add_perms(ListTemplate, ['view'])
        add_perms(Person, ['add', 'change', 'view'])

        group.permissions.set(permissions_to_add)
        
        self.stdout.write(self.style.SUCCESS(f'Successfully updated group "{group.name}" with {len(permissions_to_add)} permissions.'))
