from django import forms

from .models import AdoptionApplication, Animal


class AdoptionApplicationForm(forms.ModelForm):
    class Meta:
        model = AdoptionApplication
        # The animal comes from the URL and employees set the status in the
        # admin, so neither is a form field.
        fields = ["applicant_name", "email", "phone", "message"]
        labels = {
            "applicant_name": "Your name",
            "message": "Tell us about your home",
        }


class AnimalSearchForm(forms.Form):
    """The list page's search. It saves nothing: the list view reads it from
    the query string, so a search can be bookmarked and paged."""

    name = forms.CharField(required=False)
    species = forms.ChoiceField(
        choices=[("", "All species"), *Animal.Species.choices], required=False
    )
