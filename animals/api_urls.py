from rest_framework.routers import DefaultRouter

from . import api

# The router writes the routes for each viewset it is given, and a root page
# at /api/v1/ that links to them.
router = DefaultRouter()
router.register("animals", api.AnimalViewSet)

urlpatterns = router.urls
