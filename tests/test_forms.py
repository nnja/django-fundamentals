import pytest
from django.urls import reverse
from pytest_django.asserts import assertRedirects

from animals.forms import AdoptionApplicationForm
from animals.models import AdoptionApplication, Animal

pytestmark = pytest.mark.django_db

VALID_FORM = {
    "applicant_name": "Maria",
    "email": "maria@example.com",
    "phone": "555-010-2000",
    "message": "We have a fenced yard.",
}


def test_form_has_only_the_applicant_fields():
    assert list(AdoptionApplicationForm().fields) == [
        "applicant_name",
        "email",
        "phone",
        "message",
    ]


def test_adopt_page_shows_the_form(client, make_animal):
    animal = make_animal(name="Clover")
    response = client.get(reverse("animals:adopt", args=[animal.pk]))
    content = response.content.decode()
    assert response.status_code == 200
    assert "Clover" in content
    for field in VALID_FORM:
        assert f'name="{field}"' in content
    assert "csrfmiddlewaretoken" in content


def test_valid_post_saves_the_application_and_thanks_the_visitor_once(
    client, make_animal
):
    animal = make_animal(name="Clover")
    detail = reverse("animals:detail", args=[animal.pk])
    # follow=True loads the page the redirect points to, as a browser does.
    response = client.post(
        reverse("animals:adopt", args=[animal.pk]), VALID_FORM, follow=True
    )
    assertRedirects(response, detail)
    application = AdoptionApplication.objects.get()
    assert application.animal == animal
    assert application.applicant_name == "Maria"
    assert application.status == AdoptionApplication.Status.SUBMITTED
    thanks = "Thanks! We have your application for Clover."
    assert thanks in response.content.decode()
    # The message is shown once: loading the page again does not repeat it.
    assert thanks not in client.get(detail).content.decode()


def test_invalid_post_shows_errors_and_saves_nothing(client, make_animal):
    animal = make_animal()
    data = {**VALID_FORM, "email": "not-an-email"}
    response = client.post(reverse("animals:adopt", args=[animal.pk]), data)
    assert response.status_code == 200
    assert "Enter a valid email address." in response.content.decode()
    assert AdoptionApplication.objects.count() == 0


def test_adopt_rejects_unavailable_animal(client, make_animal):
    adopted = make_animal(status=Animal.Status.ADOPTED)
    pending = make_animal(status=Animal.Status.PENDING)
    for animal_id in [adopted.pk, pending.pk, 999]:
        url = reverse("animals:adopt", args=[animal_id])
        assert client.get(url).status_code == 404
        assert client.post(url, VALID_FORM).status_code == 404
    assert AdoptionApplication.objects.count() == 0


def test_detail_page_links_to_the_form_only_when_available(client, make_animal):
    available = make_animal()
    pending = make_animal(status=Animal.Status.PENDING)
    available_page = client.get(reverse("animals:detail", args=[available.pk]))
    pending_page = client.get(reverse("animals:detail", args=[pending.pk]))
    assert (
        reverse("animals:adopt", args=[available.pk]) in available_page.content.decode()
    )
    assert (
        reverse("animals:adopt", args=[pending.pk]) not in pending_page.content.decode()
    )
