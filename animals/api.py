from rest_framework import viewsets

from . import queries
from .serializers import AnimalSerializer


class AnimalViewSet(viewsets.ReadOnlyModelViewSet):
    """Every animal, newest arrivals first.

    Anyone can read this API: DRF's default permission, AllowAny, lets every
    request through. A production API would usually require a login or rate
    limiting.

    Add an animal's id to the address for one animal, or ?species=rabbit
    for one species.
    """

    queryset = queries.all_animals()
    serializer_class = AnimalSerializer

    def get_queryset(self):
        animals = super().get_queryset()
        species = self.request.query_params.get("species")
        if species:
            animals = queries.of_species(animals, species)
        return animals
