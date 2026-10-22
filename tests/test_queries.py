import datetime as dt

import pytest

from animals import queries
from animals.models import Animal

pytestmark = pytest.mark.django_db

TODAY = dt.date.today()


def test_available_animals_newest_first_and_only_available(make_animal):
    older = make_animal(name="Older", intake_date=TODAY - dt.timedelta(days=10))
    newer = make_animal(name="Newer", intake_date=TODAY - dt.timedelta(days=1))
    make_animal(name="Gone", status=Animal.Status.ADOPTED)
    make_animal(name="Held", status=Animal.Status.PENDING)
    assert list(queries.available_animals()) == [newer, older]


def test_listed_animals_excludes_adopted_only_newest_first(make_animal):
    available = make_animal(name="A", intake_date=TODAY - dt.timedelta(days=3))
    pending = make_animal(name="B", status=Animal.Status.PENDING)
    make_animal(name="C", status=Animal.Status.ADOPTED)
    assert list(queries.listed_animals()) == [pending, available]


def test_youngest_first_sorts_the_latest_birth_date_first(make_animal):
    older = make_animal(name="Older", birth_date=TODAY - dt.timedelta(days=400))
    younger = make_animal(name="Younger", birth_date=TODAY - dt.timedelta(days=30))
    animals = queries.youngest_first(queries.listed_animals())
    assert list(animals) == [younger, older]


def test_named_is_a_case_insensitive_substring_match(make_animal):
    biscuit = make_animal(name="Biscuit")
    make_animal(name="Clover")
    assert list(queries.named(queries.listed_animals(), "CUI")) == [biscuit]


def test_of_species_keeps_only_that_species(make_animal):
    clover = make_animal(name="Clover", species=Animal.Species.RABBIT)
    make_animal(name="Biscuit")
    rabbits = queries.of_species(queries.listed_animals(), Animal.Species.RABBIT)
    assert list(rabbits) == [clover]
