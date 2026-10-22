from django.core.exceptions import ValidationError
from django.forms import BaseInlineFormSet

from .models import AdoptionApplication


class OneApprovalFormSet(BaseInlineFormSet):
    """Refuses a save that approves more than one application for an animal.

    Django calls the rows of an inline a formset. AdoptionApplication.clean()
    checks one application against those already in the database. When two
    existing rows are changed to approved in one save, neither new status is
    in the database yet, so each passes. This clean() runs once for the whole
    table and counts them.
    """

    def clean(self):
        super().clean()
        if any(self.errors):
            # A row is already refused; its own message is enough.
            return
        approved = [
            form
            for form in self.forms
            if form.cleaned_data.get("status") == AdoptionApplication.Status.APPROVED
            # A row ticked for deletion will not be there after the save.
            and not self._should_delete_form(form)
        ]
        if len(approved) > 1:
            raise ValidationError(
                "Only one application per animal can be approved. "
                "Approve one and save, or decline the others."
            )
