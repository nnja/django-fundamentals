from django.contrib import admin

from .formsets import OneApprovalFormSet
from .models import AdoptionApplication, Animal

# The admin's header, the browser tab's title, and the index page's heading.
admin.site.site_header = "RescueScout"
admin.site.site_title = "RescueScout admin"
admin.site.index_title = "Animals and applications"


# admin.TabularInline shows an animal's applications as rows of a table on
# the animal's own admin page. Someone without permission to view
# applications doesn't see the table.
class AdoptionApplicationInline(admin.TabularInline):
    model = AdoptionApplication
    # A review table: who applied, how to reach them, and the status to set.
    fields = ["applicant_name", "email", "status"]
    readonly_fields = ["applicant_name", "email"]
    # A link from each row to the application's own page.
    show_change_link = True
    # extra is how many empty rows the table shows for adding applications.
    # The default is 3. Visitors create applications, so show none.
    extra = 0
    # Refuses a save that approves two applications at once.
    formset = OneApprovalFormSet

    def has_add_permission(self, request, obj):
        # Applications come from visitors, so the table has no row for adding one.
        return False


@admin.register(Animal)
class AnimalAdmin(admin.ModelAdmin):
    list_display = ["name", "species", "breed", "status", "intake_date"]
    list_filter = ["species", "status"]
    search_fields = ["name", "breed"]
    # The animal search box on an application pages through this admin's
    # animals, and a page is only stable when the order leaves no ties.
    ordering = ["name", "id"]
    inlines = [AdoptionApplicationInline]

    def get_readonly_fields(self, request, obj=None):
        """Without manage_animal, the status is read-only."""
        fields = list(super().get_readonly_fields(request, obj))
        # has_perm() names a permission by its app's label and its codename.
        if not request.user.has_perm("animals.manage_animal"):
            # A read-only field isn't in the form, so a new animal gets the
            # model's default status.
            fields.append("status")
        return fields

    def has_change_permission(self, request, obj=None):
        """Without manage_animal, an adopted animal can't be changed."""
        # obj is None when Django asks about the model as a whole, as the
        # admin's index and list pages do.
        if (
            obj is not None
            and obj.status == Animal.Status.ADOPTED
            and not request.user.has_perm("animals.manage_animal")
        ):
            return False
        return super().has_change_permission(request, obj)


@admin.register(AdoptionApplication)
class AdoptionApplicationAdmin(admin.ModelAdmin):
    list_display = ["applicant_name", "animal", "status", "created_at"]
    list_filter = ["status"]
    # A search box for the animal, in place of a menu listing every animal.
    autocomplete_fields = ["animal"]
    # animal__name is the name of the application's animal, read through
    # the foreign key, so searching for an animal's name finds its
    # applications.
    search_fields = ["applicant_name", "email", "animal__name"]
