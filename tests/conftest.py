"""Fixtures shared by every test module. pytest-django supplies the rest:
`client`, `admin_client`, `settings`, and `django_user_model`."""

import datetime as dt
import io

import pytest
from PIL import Image

from animals.models import AdoptionApplication, Animal


def png_bytes(color="#f2a93b"):
    """A 4x4 PNG, enough for an ImageField to accept."""
    buffer = io.BytesIO()
    Image.new("RGB", (4, 4), color).save(buffer, format="PNG")
    return buffer.getvalue()


@pytest.fixture
def pin_today(monkeypatch):
    """Make date.today() return a chosen day wherever the application asks for it."""

    def pin(year, month, day):
        class PinnedDate(dt.date):
            @classmethod
            def today(cls):
                return dt.date(year, month, day)

        # animals.models imported the name `date`, so it holds its own reference.
        monkeypatch.setattr("animals.models.date", PinnedDate)
        return dt.date(year, month, day)

    return pin


@pytest.fixture
def make_animal(db):
    """Create an available adult dog named Biscuit; override any field by keyword."""

    def factory(**overrides):
        values = {
            "name": "Biscuit",
            "species": Animal.Species.DOG,
            "breed": "Beagle mix",
            "birth_date": dt.date.today() - dt.timedelta(days=3 * 365),
            "description": "A gentle dog who likes long walks.",
            "status": Animal.Status.AVAILABLE,
        }
        values.update(overrides)
        return Animal.objects.create(**values)

    return factory


@pytest.fixture
def make_application(make_animal):
    """Create a submitted application from Maria for a new or given animal."""

    def factory(animal=None, **overrides):
        values = {
            "applicant_name": "Maria",
            "email": "maria@example.com",
            "phone": "555-010-2000",
            "message": "We have a fenced yard and no other pets.",
        }
        values.update(overrides)
        return AdoptionApplication.objects.create(
            animal=animal or make_animal(), **values
        )

    return factory


@pytest.fixture
def media_root(settings, tmp_path):
    """Point uploads at a temporary directory so tests never write into media/."""
    settings.MEDIA_ROOT = tmp_path / "media"
    return settings.MEDIA_ROOT
