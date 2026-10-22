from datetime import date, timedelta

from django.core.exceptions import ValidationError
from django.db import models

from .validators import validate_phone

# What to call an animal under a year old, by species.
YOUNG_LABELS = {"dog": "Puppy", "cat": "Kitten", "rabbit": "Bunny"}


class Animal(models.Model):
    """One animal in the rescue's care, from intake until adoption.

    The public list leaves out adopted animals. A visitor can apply only
    for an available animal, through the site's form. For a stray, the
    birth date is an estimate.
    """

    class Species(models.TextChoices):
        DOG = "dog", "Dog"
        CAT = "cat", "Cat"
        RABBIT = "rabbit", "Rabbit"

    class Status(models.TextChoices):
        AVAILABLE = "available", "Available"
        PENDING = "pending", "Adoption pending"
        ADOPTED = "adopted", "Adopted"

    name = models.CharField(max_length=100)
    species = models.CharField(max_length=10, choices=Species)
    breed = models.CharField(max_length=100, blank=True)
    birth_date = models.DateField()
    description = models.TextField(blank=True)
    # The column holds a path under MEDIA_ROOT, such as animals/biscuit.jpg,
    # not the image itself. ImageField needs the Pillow package, which Django
    # uses to check that an upload really is an image.
    photo = models.ImageField(upload_to="animals/", blank=True)
    status = models.CharField(max_length=10, choices=Status, default=Status.AVAILABLE)
    intake_date = models.DateField(default=date.today)

    class Meta:
        # Django gives every model four permissions: add, change, delete, and
        # view. This adds a fifth: a codename, and the label the admin shows.
        permissions = [
            (
                "manage_animal",
                "Can change an animal's status, and change adopted animals",
            ),
        ]

    def __str__(self):
        return self.name

    def age_label(self):
        """Puppy, Kitten, or Bunny under a year old; otherwise Adult."""
        if self.birth_date > date.today() - timedelta(days=365):
            # save() does not check choices, so the species may not be listed.
            return YOUNG_LABELS.get(self.species, "Young")
        return "Adult"


class AdoptionApplication(models.Model):
    """One visitor's request to adopt one animal.

    An employee approves or declines it in the admin. Approving one marks
    its animal pending, and a visitor cannot apply for a pending animal.
    """

    class Status(models.TextChoices):
        SUBMITTED = "submitted", "Submitted"
        APPROVED = "approved", "Approved"
        DECLINED = "declined", "Declined"

    # related_name is what animal.applications.all() reads from.
    animal = models.ForeignKey(
        Animal, on_delete=models.CASCADE, related_name="applications"
    )
    applicant_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(
        max_length=20,
        blank=True,
        help_text="A US number, like 555-010-2000",
        validators=[validate_phone],
    )
    message = models.TextField(blank=True)
    status = models.CharField(max_length=10, choices=Status, default=Status.SUBMITTED)
    # Set once, when the row is first saved.
    created_at = models.DateTimeField("submitted time", auto_now_add=True)

    def __str__(self):
        return f"{self.applicant_name} for {self.animal}"

    def save(self, **kwargs):
        super().save(**kwargs)
        # An approved application marks its animal pending.
        if (
            self.status == self.Status.APPROVED
            and self.animal.status == Animal.Status.AVAILABLE
        ):
            self.animal.status = Animal.Status.PENDING
            # Write the status column only, not the whole animal record.
            self.animal.save(update_fields=["status"])

    def clean(self):
        """Refuse a second approval for an animal; forms and the admin call this."""
        # A form calls clean() even when its animal field was refused, and an
        # application with no animal has nothing to compare against.
        if self.status != self.Status.APPROVED or self.animal_id is None:
            return
        others = self.animal.applications.filter(status=self.Status.APPROVED)
        if others.exclude(pk=self.pk).exists():
            # The error names no field, so it is about the whole application.
            # An error tied to a field raises ValueError in a form without
            # that field, and the public form has no status field.
            raise ValidationError(
                "Another application for this animal is already approved."
            )
