from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from core.models import ListCategory, BucketList, ListItem
from django.db import transaction

class Command(BaseCommand):
    help = 'Seeds beautiful demo lists and items for testing the tracker templates'

    def handle(self, *args, **options):
        # Find a user to own the lists
        owner = User.objects.filter(is_superuser=True).first() or User.objects.first()
        if not owner:
            owner = User.objects.create_superuser('admin', 'admin@example.com', 'admin')
            self.stdout.write(self.style.SUCCESS("Created superuser 'admin'"))

        with transaction.atomic():
            # 1. Medikamentenplan
            cat_med = ListCategory.objects.filter(name='Medikamentenplan').first()
            if cat_med:
                list_med, created = BucketList.objects.get_or_create(
                    title="💊 Mein Medikamentenplan",
                    category=cat_med,
                    owner=owner
                )
                if created or not list_med.items.exists():
                    ListItem.objects.create(
                        bucket_list=list_med,
                        title="Ibuprofen 400mg",
                        brand="Hexal",
                        tracker_unit="Tablette",
                        tracker_times="08:00, 20:00",
                        tracker_stock_total=50,
                        tracker_stock_min=10,
                        notes="Bei Bedarf nach dem Essen einnehmen."
                    )
                    ListItem.objects.create(
                        bucket_list=list_med,
                        title="L-Thyroxin 50",
                        brand="Henning",
                        tracker_unit="Tablette",
                        tracker_times="07:00",
                        tracker_stock_total=100,
                        tracker_stock_min=14,
                        notes="30 Minuten vor dem Frühstück mit stillem Wasser einnehmen."
                    )
                    self.stdout.write(self.style.SUCCESS("Seeded Medikamentenplan demo list"))

            # 2. Haustier-Planer
            cat_pet = ListCategory.objects.filter(name='Haustier-Planer').first()
            if cat_pet:
                list_pet, created = BucketList.objects.get_or_create(
                    title="🐾 Haustier-Planer (Bello & Minka)",
                    category=cat_pet,
                    owner=owner
                )
                if created or not list_pet.items.exists():
                    ListItem.objects.create(
                        bucket_list=list_pet,
                        title="Bello füttern",
                        brand="Nassfutter (Rind)",
                        tracker_unit="Dose Nassfutter",
                        tracker_times="07:30, 18:30",
                        tracker_stock_total=24,
                        tracker_stock_min=6,
                        notes="Dosen stehen im Vorratskeller. Immer mit frischem Wasser servieren."
                    )
                    ListItem.objects.create(
                        bucket_list=list_pet,
                        title="Katze Minka füttern",
                        brand="Trockenfutter",
                        tracker_unit="Portion",
                        tracker_times="08:00, 19:00",
                        tracker_stock_total=40,
                        tracker_stock_min=8,
                        notes="Portionslöffel liegt im Trockenfutter-Beutel."
                    )
                    self.stdout.write(self.style.SUCCESS("Seeded Haustier-Planer demo list"))

            # 3. Pflanzen-Pflege
            cat_plant = ListCategory.objects.filter(name='Pflanzen-Pflege').first()
            if cat_plant:
                list_plant, created = BucketList.objects.get_or_create(
                    title="🪴 Pflanzen-Pflege (Wohnzimmer)",
                    category=cat_plant,
                    owner=owner
                )
                if created or not list_plant.items.exists():
                    ListItem.objects.create(
                        bucket_list=list_plant,
                        title="Bonsai gießen",
                        brand="Regenwasser",
                        tracker_unit="Gießkanne",
                        tracker_times="09:00",
                        tracker_stock_total=15,
                        tracker_stock_min=3,
                        notes="Erde feucht halten, Staunässe vermeiden."
                    )
                    self.stdout.write(self.style.SUCCESS("Seeded Pflanzen-Pflege demo list"))

            # 4. Trainingsplan
            cat_gym = ListCategory.objects.filter(name='Trainingsplan').first()
            if cat_gym:
                list_gym, created = BucketList.objects.get_or_create(
                    title="🏋️‍♂️ Mein Ganzkörper-Trainingsplan",
                    category=cat_gym,
                    owner=owner
                )
                if created or not list_gym.items.exists():
                    # Strength exercise
                    ListItem.objects.create(
                        bucket_list=list_gym,
                        title="Bankdrücken",
                        workout_type="strength",
                        workout_config_json={
                            "sets_count": 3,
                            "target_reps": "10, 8, 6",
                            "target_weight": "60",
                            "rest_time": 90
                        },
                        notes="Fokus auf saubere Ausführung und kontrolliertes Absenken."
                    )
                    # Interval exercise
                    ListItem.objects.create(
                        bucket_list=list_gym,
                        title="Tabata Kettlebell-Swings",
                        workout_type="interval",
                        workout_config_json={
                            "interval_format": "Tabata",
                            "interval_duration": 4
                        },
                        notes="20 Sek Belastung, 10 Sek Pause im Wechsel für 8 Runden."
                    )
                    # Endurance exercise
                    ListItem.objects.create(
                        bucket_list=list_gym,
                        title="Waldlauf (Grundlagenausdauer)",
                        workout_type="endurance",
                        workout_config_json={
                            "target_distance": "5",
                            "target_duration": "30",
                            "target_pace": "6.0"
                        },
                        notes="Konstantes Tempo halten, lockerer Lauf."
                    )
                    self.stdout.write(self.style.SUCCESS("Seeded Trainingsplan demo list"))

        self.stdout.write(self.style.SUCCESS("Demo data seeded successfully!"))
