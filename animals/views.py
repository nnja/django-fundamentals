import logging

from django.contrib import messages
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.views.generic import CreateView, DetailView, ListView, TemplateView

from . import queries
from .forms import AdoptionApplicationForm, AnimalSearchForm
from .models import AdoptionApplication, Animal

logger = logging.getLogger(__name__)


class AnimalListView(ListView):
    """Animals looking for a home, newest arrivals first.

    The search form narrows them by name and species, and with
    ?sort=youngest, the youngest animals come first.
    """

    # Twelve cards fill three rows of the grid at desktop width.
    paginate_by = 12

    def get_queryset(self):
        animals = queries.listed_animals()
        self.form = AnimalSearchForm(self.request.GET)
        # An invalid search, such as a species that isn't one of the
        # choices, narrows nothing; the template shows the form's error.
        if self.form.is_valid():
            name = self.form.cleaned_data["name"]
            if name:
                animals = queries.named(animals, name)
            species = self.form.cleaned_data["species"]
            if species:
                animals = queries.of_species(animals, species)
        self.sort = self.request.GET.get("sort")
        if self.sort == "youngest":
            animals = queries.youngest_first(animals)
        return animals

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form"] = self.form
        context["sort"] = self.sort
        return context


class AnimalDetailView(DetailView):
    model = Animal


class AboutView(TemplateView):
    template_name = "animals/about.html"
    extra_context = {"name": "RescueScout"}


class AdoptView(CreateView):
    """The application form for an available animal. Any other animal is a 404."""

    model = AdoptionApplication
    form_class = AdoptionApplicationForm
    template_name = "animals/adopt.html"

    # dispatch() calls get() or post(), so both have self.animal.
    def dispatch(self, request, *args, **kwargs):
        self.animal = get_object_or_404(
            queries.available_animals(), pk=kwargs["animal_id"]
        )
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["animal"] = self.animal
        return context

    def form_valid(self, form):
        # The form never saw the animal, so set it before the row is written.
        form.instance.animal = self.animal
        # Saves the application as self.object and redirects to get_success_url().
        response = super().form_valid(form)
        # Ids only: personal info about who applied shouldn't be logged.
        logger.info(
            "Adoption application %s saved for animal %s",
            self.object.pk,
            self.animal.pk,
        )
        # Shown once, on the next page the visitor loads.
        messages.success(
            self.request, f"Thanks! We have your application for {self.animal.name}."
        )
        return response

    def get_success_url(self):
        return reverse("animals:detail", kwargs={"pk": self.animal.pk})
