from core.models import ListCategory, BucketList
from django.db import transaction

def cleanup_categories():
    mapping = {
        '🛒 Einkauf': 'Einkaufsliste',
        '✅ To-Do': 'To-Do Liste',
        '🍷 Weinliste': 'Weinvorrat',
        '🤝 Verliehen': 'Wunschliste', # Map to something similar
        '🪣 Bucket List': 'To-Do Liste',
    }
    
    with transaction.atomic():
        for old_name, new_name in mapping.items():
            old_cat = ListCategory.objects.filter(name=old_name).first()
            new_cat = ListCategory.objects.filter(name=new_name).first()
            
            if old_cat and new_cat:
                # Reassign lists
                BucketList.objects.filter(category=old_cat).update(category=new_cat)
                # Delete old category
                old_cat.delete()
                print(f"Migrated and deleted: {old_name} -> {new_name}")
            elif old_cat:
                # If no new cat exists (shouldn't happen with our seed), just delete if unused
                try:
                    old_cat.delete()
                    print(f"Deleted unused old category: {old_name}")
                except Exception:
                    print(f"Could not delete {old_name} (still in use)")

        # Final check for any category with icon 📋
        for cat in ListCategory.objects.filter(icon='📋'):
            try:
                cat.delete()
                print(f"Deleted remaining 📋 category: {cat.name}")
            except Exception:
                print(f"Skipped {cat.name} (in use)")

if __name__ == '__main__':
    cleanup_categories()
