import pytest
from django.core.exceptions import ValidationError
from django.urls import reverse

from animals.models import AdoptionApplication
from animals.validators import validate_phone

pytestmark = pytest.mark.django_db

ERROR = "Enter a 10-digit US phone number, like 555-010-2000."
BAD_PHONE = "555-1234"
APPLICANT = {
    "applicant_name": "Maria",
    "email": "maria@example.com",
    "phone": BAD_PHONE,
    "message": "",
}


@pytest.mark.parametrize(
    "value",
    [
        "555-010-2000",
        "(555) 010-2000",
        "555 010 2000",
        "5550102000",
    ],
)
def test_validator_accepts_ten_digit_us_numbers(value):
    validate_phone(value)


@pytest.mark.parametrize(
    "value",
    [
        "555-1234",
        "555-010-20000",
        # A country code makes eleven digits.
        "1-555-010-2000",
        "555.010.2000",
        # One parenthesis without the other.
        "(5550102000",
        "555-010-2000 ext 4",
        "555-010-2000\n",
        # Arabic-Indic digits, which \d matches.
        "\u0665\u0665\u0665\u0660\u0661\u0660\u0662\u0660\u0660\u0660",
    ],
)
def test_validator_rejects_anything_but_ten_digits(value):
    with pytest.raises(ValidationError, match="10-digit US phone number"):
        validate_phone(value)


def test_same_bad_phone_rejected_by_the_form_and_the_admin(
    client, admin_client, make_animal
):
    animal = make_animal()

    form_response = client.post(reverse("animals:adopt", args=[animal.pk]), APPLICANT)
    assert form_response.status_code == 200
    assert ERROR in form_response.content.decode()

    admin_response = admin_client.post(
        reverse("admin:animals_adoptionapplication_add"),
        {**APPLICANT, "animal": animal.pk, "status": "submitted"},
    )
    assert admin_response.status_code == 200
    assert ERROR in admin_response.content.decode()
    assert AdoptionApplication.objects.count() == 0
