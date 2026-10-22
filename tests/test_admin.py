import pytest
from django.contrib.auth.models import Group, Permission
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client
from django.urls import reverse

from animals.management.commands.seed import GROUPS
from animals.models import AdoptionApplication, Animal
from tests.conftest import png_bytes

pytestmark = pytest.mark.django_db


def animal_form_data(animal, rows):
    """What the animal page posts: its own fields, then one inline row per
    (application id, status) pair. An id of None is a row added on the page."""
    data = {
        "name": animal.name,
        "species": animal.species,
        "breed": animal.breed,
        "birth_date": animal.birth_date.isoformat(),
        "description": animal.description,
        "status": animal.status,
        "intake_date": animal.intake_date.isoformat(),
        "applications-TOTAL_FORMS": str(len(rows)),
        "applications-INITIAL_FORMS": str(sum(1 for pk, _ in rows if pk)),
        "applications-MIN_NUM_FORMS": "0",
        "applications-MAX_NUM_FORMS": "1000",
    }
    for index, (pk, status) in enumerate(rows):
        data[f"applications-{index}-id"] = pk or ""
        data[f"applications-{index}-animal"] = animal.pk
        data[f"applications-{index}-status"] = status
    return data


def test_photo_can_be_uploaded_through_the_admin(admin_client, make_animal, media_root):
    animal = make_animal()
    url = reverse("admin:animals_animal_change", args=[animal.pk])
    photo = SimpleUploadedFile("biscuit.png", png_bytes(), "image/png")
    data = animal_form_data(animal, []) | {"photo": photo}
    assert admin_client.post(url, data).status_code == 302
    animal.refresh_from_db()
    assert animal.photo.name == "animals/biscuit.png"
    assert (media_root / "animals" / "biscuit.png").exists()


# --- The applications table on an animal's page ---


def test_inline_ignores_a_posted_new_row(admin_client, make_animal):
    animal = make_animal()
    url = reverse("admin:animals_animal_change", args=[animal.pk])
    response = admin_client.post(url, animal_form_data(animal, [(None, "submitted")]))
    assert response.status_code == 302
    assert AdoptionApplication.objects.count() == 0


def test_inline_refuses_two_approvals_in_one_save(
    admin_client, make_animal, make_application
):
    animal = make_animal()
    first = make_application(animal=animal)
    second = make_application(animal=animal, applicant_name="Sam")
    url = reverse("admin:animals_animal_change", args=[animal.pk])
    rows = [(first.pk, "approved"), (second.pk, "approved")]
    response = admin_client.post(url, animal_form_data(animal, rows))
    assert response.status_code == 200
    assert "Only one application per animal can be approved" in (
        response.content.decode()
    )
    statuses = set(AdoptionApplication.objects.values_list("status", flat=True))
    assert statuses == {AdoptionApplication.Status.SUBMITTED}
    animal.refresh_from_db()
    assert animal.status == Animal.Status.AVAILABLE


# --- Volunteers and employees ---


def group_client(django_user_model, group_name):
    """A client logged in as an account in one of the seed's groups."""
    group = Group.objects.create(name=group_name)
    group.permissions.set(
        Permission.objects.filter(
            content_type__app_label="animals", codename__in=GROUPS[group_name]
        )
    )
    user = django_user_model.objects.create_user(group_name.lower(), is_staff=True)
    user.groups.add(group)
    client = Client()
    client.force_login(user)
    return client


@pytest.fixture
def volunteer_client(django_user_model):
    return group_client(django_user_model, "Volunteers")


@pytest.fixture
def employee_client(django_user_model):
    return group_client(django_user_model, "Employees")


def test_volunteers_dont_see_applications(volunteer_client, make_application):
    application = make_application()
    index = volunteer_client.get(reverse("admin:index")).content.decode()
    assert "Animals" in index
    assert "Adoption applications" not in index
    changelist = reverse("admin:animals_adoptionapplication_changelist")
    assert volunteer_client.get(changelist).status_code == 403
    url = reverse("admin:animals_animal_change", args=[application.animal.pk])
    content = volunteer_client.get(url).content.decode()
    assert "applications-TOTAL_FORMS" not in content
    assert "Maria" not in content


def test_a_volunteer_adds_an_animal_and_it_starts_available(volunteer_client):
    url = reverse("admin:animals_animal_add")
    assert 'name="status"' not in volunteer_client.get(url).content.decode()
    data = {
        "name": "Clover",
        "species": "rabbit",
        "breed": "Holland lop",
        "birth_date": "2026-03-01",
        "description": "",
        "intake_date": "2026-10-01",
        # Not on the form, so it's ignored.
        "status": "adopted",
    }
    assert volunteer_client.post(url, data).status_code == 302
    assert Animal.objects.get(name="Clover").status == Animal.Status.AVAILABLE


def test_a_volunteer_changes_an_animal_but_not_its_status(
    volunteer_client, make_animal
):
    animal = make_animal()
    url = reverse("admin:animals_animal_change", args=[animal.pk])
    content = volunteer_client.get(url).content.decode()
    assert 'name="name"' in content
    assert 'name="status"' not in content
    data = animal_form_data(animal, [])
    data |= {"breed": "Basset hound", "status": "adopted"}
    assert volunteer_client.post(url, data).status_code == 302
    animal.refresh_from_db()
    assert animal.breed == "Basset hound"
    assert animal.status == Animal.Status.AVAILABLE


def test_an_adopted_animal_is_read_only_for_a_volunteer(volunteer_client, make_animal):
    animal = make_animal(status=Animal.Status.ADOPTED)
    url = reverse("admin:animals_animal_change", args=[animal.pk])
    response = volunteer_client.get(url)
    # The view permission still shows the page, with every field as text.
    assert response.status_code == 200
    assert 'name="name"' not in response.content.decode()
    data = animal_form_data(animal, []) | {"breed": "Basset hound"}
    assert volunteer_client.post(url, data).status_code == 403
    animal.refresh_from_db()
    assert animal.breed == "Beagle mix"


def test_an_employee_changes_an_animals_status(employee_client, make_animal):
    animal = make_animal()
    url = reverse("admin:animals_animal_change", args=[animal.pk])
    assert 'name="status"' in employee_client.get(url).content.decode()
    data = animal_form_data(animal, []) | {"status": "adopted"}
    assert employee_client.post(url, data).status_code == 302
    animal.refresh_from_db()
    assert animal.status == Animal.Status.ADOPTED


def test_an_employee_changes_an_adopted_animal(employee_client, make_animal):
    animal = make_animal(status=Animal.Status.ADOPTED)
    url = reverse("admin:animals_animal_change", args=[animal.pk])
    data = animal_form_data(animal, []) | {"breed": "Basset hound"}
    assert employee_client.post(url, data).status_code == 302
    animal.refresh_from_db()
    assert animal.breed == "Basset hound"


def test_an_employee_approves_in_the_table_on_the_animals_page(
    employee_client, make_animal, make_application
):
    animal = make_animal()
    application = make_application(animal=animal)
    url = reverse("admin:animals_animal_change", args=[animal.pk])
    content = employee_client.get(url).content.decode()
    assert 'name="applications-0-status"' in content
    # Employees can't delete applications, so the table has no delete box.
    assert 'name="applications-0-DELETE"' not in content
    rows = [(application.pk, "approved")]
    assert employee_client.post(url, animal_form_data(animal, rows)).status_code == 302
    application.refresh_from_db()
    animal.refresh_from_db()
    assert application.status == AdoptionApplication.Status.APPROVED
    assert animal.status == Animal.Status.PENDING
