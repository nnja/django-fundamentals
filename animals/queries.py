"""Questions asked of the database, one function each.

Each returns a QuerySet that a caller can page through or loop over.
"""

from .models import Animal


def all_animals():
    """Every animal, newest arrivals first.

    The id ends the ordering so that no two rows tie. Tied rows can come
    back in any order, which would shuffle animals between pages.
    """
    return Animal.objects.order_by("-intake_date", "name", "id")


def available_animals():
    """Animals a visitor can apply for, newest arrivals first."""
    return all_animals().filter(status=Animal.Status.AVAILABLE)


def listed_animals():
    """Animals the public site shows: every animal not yet adopted, newest first."""
    return all_animals().exclude(status=Animal.Status.ADOPTED)


def named(animals, text):
    """The same animals, narrowed to names that contain the text, in any case."""
    return animals.filter(name__icontains=text)


def of_species(animals, species):
    """The same animals, narrowed to one species."""
    # The API passes whatever the query string holds, and Postgres refuses
    # some text, such as a NUL character, with an error.
    if species not in Animal.Species.values:
        return animals.none()
    return animals.filter(species=species)


def youngest_first(animals):
    """The same animals, youngest first."""
    return animals.order_by("-birth_date", "name", "id")
