import datetime as dt

import pytest
from django.core.files.base import ContentFile
from django.urls import reverse
from pytest_django.asserts import assertTemplateUsed

from animals.models import Animal
from tests.conftest import png_bytes

pytestmark = pytest.mark.django_db


def test_list_shows_unadopted_animals_with_photos_and_links(
    client, make_animal, media_root
):
    animal = make_animal(name="Clover")
    animal.photo.save("clover.png", ContentFile(png_bytes()), save=True)
    make_animal(name="Held", status=Animal.Status.PENDING)
    make_animal(name="Gone", status=Animal.Status.ADOPTED)
    content = client.get(reverse("animals:list")).content.decode()
    assert "Clover" in content
    assert "Held" in content
    assert "Gone" not in content
    assert "/media/animals/clover.png" in content
    assert reverse("animals:detail", args=[animal.pk]) in content
    assert "Adult" in content


def test_card_without_photo_shows_the_generic_image(client, make_animal):
    make_animal(name="Clover")
    content = client.get(reverse("animals:list")).content.decode()
    assert 'src=""' not in content
    assert "/static/img/no-photo.webp" in content


def test_list_searches_by_name(client, make_animal):
    make_animal(name="Biscuit")
    make_animal(name="Biscotti", species=Animal.Species.CAT)
    make_animal(name="Clover")
    found = client.get(reverse("animals:list"), {"name": "  bisc "})
    names = {animal.name for animal in found.context["page_obj"]}
    assert names == {"Biscuit", "Biscotti"}


def test_list_filters_by_species_and_keeps_it_across_pages(client, make_animal):
    for number in range(13):
        make_animal(name=f"Dog {number:02d}")
    make_animal(name="Clover", species=Animal.Species.CAT)
    dogs = client.get(reverse("animals:list"), {"species": "dog"})
    content = dogs.content.decode()
    assert dogs.context["page_obj"].paginator.count == 13
    assert "Clover" not in content
    assert 'href="?species=dog&amp;page=2"' in content
    page_two = client.get(reverse("animals:list"), {"species": "dog", "page": 2})
    assert len(page_two.context["page_obj"]) == 1


def test_list_sorts_youngest_first(client, make_animal):
    make_animal(name="Adult")
    make_animal(name="Kitten", birth_date=dt.date.today() - dt.timedelta(days=60))
    response = client.get(reverse("animals:list"), {"sort": "youngest"})
    names = [animal.name for animal in response.context["page_obj"]]
    assert names == ["Kitten", "Adult"]


def test_list_paginates_twelve_per_page(client, make_animal):
    for number in range(13):
        make_animal(name=f"Animal {number:02d}")
    page_one = client.get(reverse("animals:list"))
    page_two = client.get(reverse("animals:list"), {"page": 2})
    assert page_one.context["page_obj"].paginator.num_pages == 2
    assert len(page_one.context["page_obj"]) == 12
    assert len(page_two.context["page_obj"]) == 1
    assert "?page=2" in page_one.content.decode()


def test_detail_page_shows_the_animal(client, make_animal):
    animal = make_animal(name="Clover", breed="Tabby", description="Loves windowsills.")
    response = client.get(reverse("animals:detail", args=[animal.pk]))
    content = response.content.decode()
    assert response.status_code == 200
    for text in ["Clover", "Tabby", "Loves windowsills.", "Adult", "Available"]:
        assert text in content


def test_detail_page_404_for_unknown_animal(client):
    assert client.get(reverse("animals:detail", args=[999])).status_code == 404


def test_description_is_plain_text_with_its_paragraphs_kept(client, make_animal):
    animal = make_animal(description="Not <b>bold</b>.\n\nAlso loves snacks.")
    content = client.get(reverse("animals:detail", args=[animal.pk])).content.decode()
    assert "<p>Not &lt;b&gt;bold&lt;/b&gt;.</p>" in content
    assert "<p>Also loves snacks.</p>" in content


def test_about_page_shows_the_name_in_its_context(client):
    response = client.get("/about/")
    assert response.status_code == 200
    assertTemplateUsed(response, "animals/about.html")
    assert response.context["name"] in response.content.decode()


def test_a_missing_page_uses_the_sites_404_page(client):
    response = client.get("/no-such-page/")
    assert response.status_code == 404
    assertTemplateUsed(response, "404.html")
    assert f'href="{reverse("animals:list")}"' in response.content.decode()
