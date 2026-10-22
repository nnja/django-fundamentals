import datetime as dt

import pytest
from django.core.files.base import ContentFile
from django.urls import reverse

from animals.models import Animal
from tests.conftest import png_bytes

pytestmark = pytest.mark.django_db

TODAY = dt.date.today()
ANIMAL_FIELDS = {
    "url",
    "id",
    "name",
    "species",
    "breed",
    "birth_date",
    "age_label",
    "description",
    "photo",
    "status",
    "intake_date",
}


def test_animal_list_returns_every_animal_newest_first(client, make_animal):
    make_animal(name="Older", intake_date=TODAY - dt.timedelta(days=10))
    make_animal(name="Gone", status=Animal.Status.ADOPTED)
    response = client.get(reverse("animal-list"))
    assert response.status_code == 200
    body = response.json()
    assert body["count"] == 2
    assert [animal["name"] for animal in body["results"]] == ["Gone", "Older"]


def test_animal_list_paginates_twelve_per_page(client, make_animal):
    for number in range(13):
        make_animal(name=f"Animal {number:02d}")
    body = client.get(reverse("animal-list")).json()
    assert len(body["results"]) == 12
    assert body["previous"] is None
    assert body["next"].endswith("/api/v1/animals/?page=2")
    assert len(client.get(body["next"]).json()["results"]) == 1


def test_animal_list_filters_by_species(client, make_animal):
    make_animal(name="Biscuit")
    make_animal(name="Rex")
    make_animal(name="Clover", species=Animal.Species.RABBIT)
    body = client.get(reverse("animal-list"), {"species": "rabbit"}).json()
    assert body["count"] == 1
    assert body["results"][0]["name"] == "Clover"


def test_animal_list_with_an_empty_or_unknown_species(client, make_animal):
    make_animal(name="Biscuit")
    make_animal(name="Clover", species=Animal.Species.RABBIT)
    url = reverse("animal-list")
    assert client.get(url, {"species": ""}).json()["count"] == 2
    assert client.get(url, {"species": "dragon"}).json()["count"] == 0
    assert client.get(url, {"species": "\x00"}).json()["count"] == 0


def test_animal_detail_fields(client, make_animal, media_root):
    animal = make_animal(name="Clover", species=Animal.Species.CAT, breed="Tabby")
    animal.photo.save("clover.png", ContentFile(png_bytes()), save=True)
    body = client.get(reverse("animal-detail", args=[animal.pk])).json()
    assert set(body) == ANIMAL_FIELDS
    assert body["name"] == "Clover"
    assert body["species"] == "cat"
    assert body["age_label"] == "Adult"
    assert body["status"] == "available"
    assert body["photo"] == "http://testserver/media/animals/clover.png"
    assert body["url"] == f"http://testserver/api/v1/animals/{animal.pk}/"


def test_animals_are_read_only(client, make_animal):
    assert client.post(reverse("animal-list"), {"name": "Nope"}).status_code == 405
