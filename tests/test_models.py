import datetime as dt

import pytest
from django.core.exceptions import NON_FIELD_ERRORS, ValidationError

from animals.models import AdoptionApplication, Animal

pytestmark = pytest.mark.django_db


def test_animal_defaults_to_available_and_arrived_today():
    # Built without the make_animal fixture, which passes a status of its own.
    animal = Animal.objects.create(
        name="Biscuit", species=Animal.Species.DOG, birth_date=dt.date(2023, 5, 1)
    )
    assert animal.status == Animal.Status.AVAILABLE
    assert animal.intake_date == dt.date.today()


@pytest.mark.parametrize(
    ("species", "label"),
    [
        (Animal.Species.DOG, "Puppy"),
        (Animal.Species.CAT, "Kitten"),
        (Animal.Species.RABBIT, "Bunny"),
    ],
)
def test_age_label_under_a_year_depends_on_species(
    make_animal, pin_today, species, label
):
    pin_today(2026, 10, 12)
    animal = make_animal(species=species, birth_date=dt.date(2026, 6, 1))
    assert animal.age_label() == label


def test_age_label_is_adult_from_365_days_old(make_animal):
    born = dt.date.today() - dt.timedelta(days=365)
    assert make_animal(birth_date=born).age_label() == "Adult"


def test_deleting_an_animal_deletes_its_applications(make_application):
    make_application().animal.delete()
    assert AdoptionApplication.objects.count() == 0


def test_approving_an_application_marks_the_animal_pending(make_application):
    application = make_application()
    application.status = AdoptionApplication.Status.APPROVED
    application.save()
    application.animal.refresh_from_db()
    assert application.animal.status == Animal.Status.PENDING


@pytest.mark.parametrize(
    "status",
    [
        AdoptionApplication.Status.SUBMITTED,
        AdoptionApplication.Status.DECLINED,
    ],
)
def test_other_statuses_leave_the_animal_alone(make_application, status):
    application = make_application()
    application.status = status
    application.save()
    application.animal.refresh_from_db()
    assert application.animal.status == Animal.Status.AVAILABLE


def test_only_one_application_per_animal_can_be_approved(make_animal, make_application):
    animal = make_animal()
    make_application(animal=animal, status=AdoptionApplication.Status.APPROVED)
    second = make_application(animal=animal, applicant_name="Sam")
    second.status = AdoptionApplication.Status.APPROVED
    with pytest.raises(ValidationError) as excinfo:
        second.full_clean()
    # The error is on the application as a whole, not on the status field.
    assert list(excinfo.value.message_dict) == [NON_FIELD_ERRORS]
    assert "already approved" in excinfo.value.message_dict[NON_FIELD_ERRORS][0]


def test_an_approved_application_still_validates_itself(make_application):
    approved = make_application(status=AdoptionApplication.Status.APPROVED)
    approved.full_clean()
