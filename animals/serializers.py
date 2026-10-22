from rest_framework import serializers

from .models import Animal


class AnimalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Animal
        # Listed one by one, so a field added to the model later is not exposed
        # by accident. age_label is a model method, which comes out read-only.
        fields = [
            # "url" is not a model field. ModelSerializer builds it: a link
            # to the animal's own detail, so a client never builds one by hand.
            "url",
            "id",
            "name",
            "species",
            "breed",
            "birth_date",
            "age_label",
            "description",
            "photo",
            "status",
            "intake_date",
        ]
