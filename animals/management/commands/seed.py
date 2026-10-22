"""Fill the database with sample animals and adoption applications.

The animals and applications are the fixed rows in ANIMALS and APPLICATIONS
below, so every run creates the same data on every machine. Each animal gets
the photo its row names in seed_photos/. An animal whose file isn't there has
no photo, and the site shows a generic image for it.

    uv run manage.py seed              # the sample data
    uv run manage.py seed --reset      # the sample data, replacing what is there
    uv run manage.py seed --accounts   # also the groups and the accounts
"""

import shutil
from datetime import date, timedelta
from pathlib import Path

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand, CommandError
from django.db import connection, transaction
from django.db.migrations.executor import MigrationExecutor

from animals.models import AdoptionApplication, Animal

# Real photos, each with the file name an animal's row in ANIMALS gives.
# Add one and run again with --reset.
SEED_PHOTOS_DIR = settings.BASE_DIR / "seed_photos"
PHOTO_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp"}

# Each group's permissions, by codename. Volunteers add and update animals.
# Employees also review applications and hold manage_animal, the permission
# declared in Animal's Meta.
GROUPS = {
    "Volunteers": ["add_animal", "change_animal", "view_animal"],
    "Employees": [
        "add_animal",
        "change_animal",
        "view_animal",
        "manage_animal",
        "change_adoptionapplication",
        "view_adoptionapplication",
    ],
}
# One account in each group: a username, a password, and the group.
ACCOUNTS = [
    ("volunteer", "rescue-volunteer", "Volunteers"),
    ("employee", "rescue-employee", "Employees"),
]

# One row per animal: its name, species, breed (empty when unknown), age in
# days, how many days ago it arrived, status, and its photo's file name in
# seed_photos/. Ages and arrivals count back from the day the command runs,
# so an animal's age label is the same whenever it is seeded.
# The rows are in the order the site lists them, newest arrival first. The
# adopted animals, which the site doesn't list, come last.
ANIMALS = [
    ("Clover", "rabbit", "Lionhead mix", 294, 3, "available", "clover.webp"),
    ("Maple", "cat", "Ragdoll mix", 232, 8, "available", "maple.webp"),
    ("Waldo", "dog", "Beagle mix", 1460, 12, "available", "waldo.webp"),
    ("Juniper", "dog", "Golden retriever mix", 226, 15, "pending", "juniper.webp"),
    ("Goose", "cat", "White short-hair", 730, 19, "available", "goose.webp"),
    ("Rosie", "dog", "Old English sheepdog", 120, 23, "available", "rosie.webp"),
    ("Seven", "dog", "White shepherd", 2630, 25, "available", "seven.webp"),
    ("Peaches", "cat", "Calico", 730, 27, "available", "peaches.webp"),
    ("Bandit", "dog", "Border collie mix", 70, 30, "available", "bandit.webp"),
    ("Mango", "cat", "Tuxedo", 2920, 34, "available", "mango.webp"),
    ("Parsley", "dog", "Pit bull mix", 150, 38, "available", "parsley.webp"),
    ("Pepper", "cat", "Black and white", 666, 41, "available", "pepper.webp"),
    ("Luna", "dog", "Havanese", 3505, 43, "available", "luna.webp"),
    ("Cobalt", "dog", "Dachshund", 3650, 45, "available", "cobalt.webp"),
    ("Bramley", "cat", "Tabby and white", 120, 49, "pending", "bramley.webp"),
    ("Nori", "rabbit", "Lionhead mix", 105, 52, "available", "nori.webp"),
    ("Saffron", "cat", "Calico", 2555, 56, "available", "saffron.webp"),
    ("Heron", "dog", "Labrador mix", 995, 60, "available", "heron.webp"),
    ("Truffle", "cat", "", 1825, 63, "available", "truffle.webp"),
    ("Finch", "dog", "", 180, 67, "available", "finch.webp"),
    ("Ivy", "rabbit", "Domestic rabbit mix", 280, 71, "available", "ivy.webp"),
    ("Barley", "cat", "Brown tabby", 4380, 75, "available", "barley.webp"),
    ("Moss", "dog", "Chihuahua mix", 1100, 80, "available", "moss.webp"),
    ("Clementine", "cat", "Brown tabby", 156, 84, "available", "clementine.webp"),
    ("Linden", "dog", "Doberman mix", 2190, 90, "available", "linden.webp"),
    ("Nutmeg", "cat", "Cream tabby", 3650, 95, "available", "nutmeg.webp"),
    ("Thistle", "rabbit", "Holland lop mix", 760, 101, "pending", "thistle.webp"),
    ("Walnut", "dog", "Brittany spaniel mix", 4015, 108, "available", "walnut.webp"),
    ("Hobbes", "cat", "", 1825, 115, "available", "hobbes.webp"),
    ("Tamarind", "dog", "Labrador retriever", 150, 122, "available", "tamarind.webp"),
    ("Tofu", "cat", "Tabby and white", 243, 130, "available", "tofu.webp"),
    ("Rowan", "dog", "Labrador mix", 500, 138, "available", "rowan.webp"),
    ("Bean", "cat", "Black and white", 2250, 147, "available", "bean.webp"),
    ("Pebble", "rabbit", "", 1460, 156, "available", "pebble.webp"),
    ("Waffles", "cat", "Persian mix", 710, 175, "available", "waffles.webp"),
    ("Kiwi", "cat", "Ragdoll mix", 1095, 198, "available", "kiwi.webp"),
    ("Radish", "dog", "German shepherd mix", 3215, 210, "available", "radish.webp"),
    ("Juno", "cat", "Brown tabby", 2685, 225, "available", "juno.webp"),
    ("Sprout", "rabbit", "Californian mix", 1825, 240, "available", "sprout.webp"),
    ("Gravy", "dog", "German shepherd mix", 3365, 260, "available", "gravy.webp"),
    ("Cedar", "cat", "Siamese mix", 3180, 285, "available", "cedar.webp"),
    ("Noodle", "dog", "Poodle mix", 2890, 310, "available", "noodle.webp"),
    ("Domino", "dog", "Bichon frise mix", 3135, 120, "adopted", "domino.webp"),
    ("Basil", "dog", "German shepherd mix", 2245, 200, "adopted", "basil.webp"),
    ("Marlow", "cat", "Brown tabby", 4310, 150, "adopted", "marlow.webp"),
    ("Otter", "cat", "", 1200, 90, "adopted", "otter.webp"),
    ("Dumpling", "rabbit", "", 900, 60, "adopted", "dumpling.webp"),
]

# Each animal's description, by name. An animal missing from here has none
# written yet.
DESCRIPTIONS = {
    "Clover": (
        "Clover is gentle and loves sunny windowsills. "
        "Clover would do best with a quiet home."
    ),
    "Maple": (
        "Maple is endlessly curious and loves chasing feather toys. "
        "Maple would do best with another cat for company."
    ),
    "Waldo": (
        "Waldo is goofy and loves long walks. Waldo would do best with a fenced yard."
    ),
    "Juniper": (
        "Juniper is playful and loves squeaky toys. "
        "Juniper would do best with someone home during the day."
    ),
    "Truffle": (
        "Truffle is calm and loves a warm lap. Truffle would do best with a quiet home."
    ),
    "Cobalt": (
        "Cobalt is easygoing and loves belly rubs. "
        "Cobalt would do best with a patient owner."
    ),
    "Seven": (
        "Seven is playful and loves to play fetch with a ball. "
        "Seven would do best with a fenced yard.\n\n"
        "Seven isn't actually up for adoption, because she's Nina's pup. "
        "Congrats! You found an easter egg."
    ),
    "Peaches": (
        "Peaches is affectionate and loves napping in cardboard boxes. "
        "Peaches would do best with another cat for company."
    ),
    "Bandit": (
        "Bandit is endlessly curious and loves chasing leaves. "
        "Bandit would do best with a patient owner."
    ),
    "Mango": (
        "Mango is independent and loves sunny windowsills. "
        "Mango would do best with a home without small children."
    ),
    "Nori": (
        "Nori is a little shy at first and loves fresh greens. "
        "Nori would do best with a quiet home."
    ),
    "Pepper": (
        "Pepper is affectionate and loves chin scratches. "
        "Pepper would do best with someone home during the day."
    ),
    "Luna": (
        "Luna was a sweet elderly Havanese pup who loved to cuddle and play "
        "with kids. She'd keep an eye on everyone from her perch on top of "
        "the couch.\n\n"
        "She belonged to instructor Brian Holt, who misses her dearly."
    ),
    "Rosie": (
        "Rosie is gentle and loves meeting new people. "
        "Rosie would do best with a fenced yard."
    ),
    "Bramley": (
        "Bramley is playful and loves puzzle feeders. "
        "Bramley would do best with another cat for company."
    ),
    "Parsley": (
        "Parsley is goofy and loves squeaky toys. "
        "Parsley would do best with a fenced yard."
    ),
    "Saffron": (
        "Saffron is calm and loves quiet mornings. "
        "Saffron would do best with a quiet home."
    ),
    "Heron": (
        "Heron is food-motivated and loves puzzle feeders. "
        "Heron would do best with an active owner."
    ),
    "Goose": (
        "Goose is endlessly curious and loves chasing leaves. "
        "Goose would do best with a patient owner."
    ),
    "Finch": (
        "Finch is a little shy at first and loves a warm lap. "
        "Finch would do best with a patient owner."
    ),
    "Ivy": (
        "Ivy is easygoing and loves fresh greens. "
        "Ivy would do best with room to hop around."
    ),
    "Barley": (
        "Barley is independent and loves sunny windowsills. "
        "Barley would do best with a home without small children."
    ),
    "Moss": (
        "Moss is affectionate and loves car rides. "
        "Moss would do best with someone home during the day.\n\n"
        "Moss came to us from an owner who could no longer manage, "
        "and is house-trained."
    ),
    "Clementine": (
        "Clementine is playful and loves chasing feather toys. "
        "Clementine would do best with another cat for company."
    ),
    "Linden": (
        "Linden is calm and loves long walks. "
        "Linden would do best with a home without other dogs."
    ),
    "Nutmeg": (
        "Nutmeg is gentle and loves chin scratches. "
        "Nutmeg would do best with a quiet home."
    ),
    "Thistle": (
        "Thistle is endlessly curious and loves cardboard tunnels. "
        "Thistle would do best with room to hop around."
    ),
    "Walnut": (
        "Walnut is easygoing and loves quiet mornings. "
        "Walnut would do best with a patient owner."
    ),
    "Hobbes": (
        "Hobbes is goofy and loves napping in cardboard boxes. "
        "Hobbes would do best with someone home during the day."
    ),
    "Tamarind": (
        "Tamarind is a little shy at first and loves a warm lap. "
        "Tamarind would do best with a quiet home."
    ),
    "Tofu": (
        "Tofu is affectionate and loves a warm lap. "
        "Tofu would do best with another cat for company.\n\n"
        "Tofu came to us from a shelter that ran out of room, "
        "and sleeps through the night."
    ),
    "Rowan": (
        "Rowan is gentle and loves belly rubs. "
        "Rowan would do best with a home without small children."
    ),
    "Bean": (
        "Bean is independent and loves sunny windowsills. "
        "Bean would do best with a patient owner."
    ),
    "Pebble": (
        "Pebble is calm and loves fresh greens. "
        "Pebble would do best with a quiet home.\n\n"
        "Pebble came to us from a family that moved away, "
        "and uses a litter box."
    ),
    "Waffles": (
        "Waffles is food-motivated and loves puzzle feeders. "
        "Waffles would do best with regular grooming."
    ),
    "Kiwi": (
        "Kiwi is easygoing and loves chin scratches. "
        "Kiwi would do best with regular grooming."
    ),
    "Juno": (
        "Juno is gentle and loves quiet mornings. Juno would do best with a quiet home."
    ),
    "Sprout": (
        "Sprout is a little shy at first and loves cardboard tunnels. "
        "Sprout would do best with a patient owner."
    ),
    "Gravy": (
        "Gravy is goofy and loves meeting new people. "
        "Gravy would do best with someone home during the day."
    ),
    "Noodle": (
        "Noodle is easygoing and loves long walks. "
        "Noodle would do best with a patient owner."
    ),
    "Domino": (
        "Domino is playful and loves chasing leaves. "
        "Domino would do best with a fenced yard."
    ),
    "Marlow": (
        "Marlow is calm and loves sunny windowsills. "
        "Marlow would do best with a quiet home."
    ),
    "Otter": (
        "Otter is affectionate and loves a warm lap. "
        "Otter would do best with another cat for company."
    ),
    "Dumpling": (
        "Dumpling is gentle and loves fresh greens. "
        "Dumpling would do best with room to hop around."
    ),
}

# One row per application: the applicant's first name, the animal's name, and
# the status. Each pending animal has one approved application, and adopted
# animals have none.
APPLICATIONS = [
    ("Jose", "Pepper", "submitted"),
    ("Priya", "Pepper", "submitted"),
    ("Aisha", "Cobalt", "submitted"),
    ("Luca", "Juniper", "approved"),
    ("Grace", "Juniper", "declined"),
    ("Noah", "Bramley", "approved"),
    ("Zoe", "Thistle", "approved"),
    ("Jordan", "Heron", "submitted"),
    ("Sam", "Nori", "declined"),
    ("Maria", "Waffles", "submitted"),
    ("Elena", "Gravy", "submitted"),
    ("Tomas", "Luna", "submitted"),
]
# The applications' messages, used in turn.
MESSAGES = [
    "We have a fenced yard and work from home most days.",
    "Our last pet passed away in the spring and the house is too quiet.",
    "I live in a one-bedroom apartment near a park and walk every morning.",
    "We have two kids who have been asking for a pet for years.",
    "I'm retired and home all day. {name} sounds like a great match for me.",
    "We already have a pet who would love a friend.",
]


def unapplied_migrations():
    """Names of migrations that migrate has not run yet."""
    executor = MigrationExecutor(connection)
    plan = executor.migration_plan(executor.loader.graph.leaf_nodes())
    return [f"{migration.app_label}.{migration.name}" for migration, _ in plan]


class Command(BaseCommand):
    help = "Load sample animals and adoption applications."

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Delete existing animals, their applications, and seeded photos first.",
        )
        parser.add_argument(
            "--accounts",
            action="store_true",
            help="Also create a superuser, the Volunteers and Employees groups, "
            "and an account in each.",
        )

    def handle(self, *args, reset, accounts, **options):
        pending = unapplied_migrations()
        if pending:
            raise CommandError(
                f"Unapplied migrations: {', '.join(pending)}. "
                "Run `uv run manage.py migrate` first."
            )

        # One transaction: a failure part-way rolls back every row written.
        # Photo files written or deleted before the failure stay as they are.
        with transaction.atomic():
            if accounts:
                self.create_demo_accounts()
            if reset:
                self.reset()
            elif Animal.objects.exists():
                self.stdout.write(
                    f"The database already has {Animal.objects.count()} animals. "
                    "Pass --reset to replace them."
                )
                return

            animals, real = self.build_animals()
            for animal in animals:
                animal.save()
            applications = self.create_applications(animals)
        self.summarize(animals, applications, real)

    def create_demo_accounts(self):
        """Accounts for the admin: a superuser, and one account in each group.
        Whatever already exists is left as it is."""
        User = get_user_model()
        made = []
        kept = []
        if User.objects.filter(username="admin").exists():
            kept.append("admin")
        else:
            # A superuser passes every permission check.
            User.objects.create_superuser("admin", "admin@example.com", "rescue-admin")
            made.append("admin / rescue-admin")
        groups = {}
        for name, codenames in GROUPS.items():
            group, created = Group.objects.get_or_create(name=name)
            if created:
                # migrate made these rows.
                group.permissions.set(
                    Permission.objects.filter(
                        content_type__app_label="animals", codename__in=codenames
                    )
                )
            groups[name] = group
        for username, password, group_name in ACCOUNTS:
            if User.objects.filter(username=username).exists():
                kept.append(username)
                continue
            # is_staff lets the account log in to the admin. What it can do
            # there comes from the group.
            account = User.objects.create_user(
                username, f"{username}@example.com", password, is_staff=True
            )
            account.groups.add(groups[group_name])
            made.append(f"{username} / {password}")
        if made:
            self.stdout.write(f"Demo accounts for the admin: {', '.join(made)}")
        if kept:
            self.stdout.write(
                f"Accounts already there, left as they were: {', '.join(kept)}"
            )

    def reset(self):
        # Deleting an animal cascades to its applications.
        deleted, _ = Animal.objects.all().delete()
        photo_dir = Path(settings.MEDIA_ROOT) / "animals"
        for path in photo_dir.glob("seed-*"):
            path.unlink()
        self.stdout.write(f"Deleted {deleted} existing rows and the seeded photos.")

    def build_animals(self):
        """An unsaved Animal for each row of ANIMALS, each with its photo.

        Returns the animals and how many photos were copied.
        """
        photo_dir = Path(settings.MEDIA_ROOT) / "animals"
        photo_dir.mkdir(parents=True, exist_ok=True)
        today = date.today()
        animals = []
        real = 0
        for row in ANIMALS:
            name, species, breed, age, arrived, status, photo = row
            animal = Animal(
                name=name,
                species=species,
                breed=breed,
                birth_date=today - timedelta(days=age),
                description=DESCRIPTIONS.get(name, ""),
                status=status,
                intake_date=today - timedelta(days=arrived),
            )
            source = SEED_PHOTOS_DIR / photo
            if source.is_file():
                shutil.copyfile(source, photo_dir / f"seed-{photo}")
                animal.photo = f"animals/seed-{photo}"
                real += 1
            animals.append(animal)
        return animals, real

    def unnamed_photos(self):
        """Photo files in seed_photos/ that no row of ANIMALS names."""
        if not SEED_PHOTOS_DIR.is_dir():
            return []
        named = {photo for *_, photo in ANIMALS}
        # Skip hidden files such as the ._name.jpg copies macOS leaves behind.
        return sorted(
            path.name
            for path in SEED_PHOTOS_DIR.iterdir()
            if path.is_file()
            and path.suffix.lower() in PHOTO_SUFFIXES
            and not path.name.startswith(".")
            and path.name not in named
        )

    def create_applications(self, animals):
        by_name = {animal.name: animal for animal in animals}
        applications = []
        for index, (applicant, animal_name, status) in enumerate(APPLICATIONS):
            animal = by_name[animal_name]
            applications.append(
                AdoptionApplication.objects.create(
                    animal=animal,
                    applicant_name=applicant,
                    email=f"{applicant.lower()}@example.com",
                    phone=f"555-010-{2001 + index}",
                    message=MESSAGES[index % len(MESSAGES)].format(name=animal.name),
                    status=status,
                )
            )
        return applications

    def summarize(self, animals, applications, real):
        by_species = {
            label.lower(): sum(1 for a in animals if a.species == value)
            for value, label in Animal.Species.choices
        }
        counts = ", ".join(
            f"{n} {label}" if n == 1 else f"{n} {label}s"
            for label, n in by_species.items()
        )
        available = sum(1 for a in animals if a.status == "available")
        self.stdout.write(
            f"Created {len(animals)} animals: {counts}. {available} available."
        )
        self.stdout.write(f"Copied {real} photo{'' if real == 1 else 's'}.")
        unnamed = self.unnamed_photos()
        if unnamed:
            files = "1 file" if len(unnamed) == 1 else f"{len(unnamed)} files"
            self.stdout.write(
                f"  {files} in seed_photos/ that no animal names: {', '.join(unnamed)}"
            )
        if not real:
            self.stdout.write(
                "  Put the photos that ANIMALS names in seed_photos/ "
                "and run again with --reset to use them."
            )
        self.stdout.write(f"Created {len(applications)} adoption applications.")
        self.stdout.write(
            "Next: uv run manage.py runserver, then open http://127.0.0.1:8000/"
        )
