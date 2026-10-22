from django.urls import path

from . import views

app_name = "animals"
urlpatterns = [
    path("", views.AnimalListView.as_view(), name="list"),
    path("about/", views.AboutView.as_view(), name="about"),
    path("animals/<int:pk>/", views.AnimalDetailView.as_view(), name="detail"),
    path("animals/<int:animal_id>/adopt/", views.AdoptView.as_view(), name="adopt"),
]
