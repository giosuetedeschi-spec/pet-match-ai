from rest_framework import serializers
from apps.core.models import AnimalImage, Animal

class AnimalImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnimalImage
        fields = ('id', 'animal', 'image', 'caption', 'is_primary', 'order')
        read_only_fields = ('id',)

    def validate_image(self, value):
        # 1. Controllo dimensione massima (es. Max 5MB)
        max_size = 5 * 1024 * 1024  # 5 Megabyte
        if value.size > max_size:
            raise serializers.ValidationError("La dimensione dell'immagine non può superare i 5MB.")

        # 2. Controllo estensione
        valid_extensions = ['.jpg', '.jpeg', '.png', '.webp']
        ext = os.path.splitext(value.name)[1].lower()
        if ext not in valid_extensions:
            raise serializers.ValidationError("Formato file non supportato. Usa JPG, PNG o WebP.")

        return value

    def validate(self, attrs):
        animal = attrs.get('animal')
        # Controllo limite massimo 10 immagini per animale
        if self.instance is None and animal:
            if animal.images.count() >= 10:
                raise serializers.ValidationError({"image": "È stato raggiunto il limite massimo di 10 foto per scheda."})
        return attrs


class BulkImageUploadSerializer(serializers.Serializer):
    images = serializers.ListField(
        child=serializers.ImageField(max_length=100000, allow_empty_file=False, use_url=False),
        write_only=True
    )

import os
from rest_framework import serializers
from apps.core.models import (
    Animal, Breed, AnimalImage, AdoptionApplication,
    ApplicationStatus, HomeVisit, Species
)
from apps.users.serializers import UserSerializer


class BreedSerializer(serializers.ModelSerializer):
    class Meta:
        model = Breed
        fields = ('id', 'species', 'name', 'description')


class AnimalImageDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnimalImage
        fields = ('id', 'image', 'caption', 'is_primary', 'order')


class AnimalSerializer(serializers.ModelSerializer):
    """
    Serializzatore in lettura per la visualizzazione dettagliata delle schede.
    """
    breed_detail = BreedSerializer(source='breed', read_only=True)
    images = AnimalImageDetailSerializer(many=True, read_only=True)
    shelter_name = serializers.CharField(source='shelter.shelter_name', read_only=True)
    city = serializers.CharField(source='shelter.user.city', read_only=True)

    class Meta:
        model = Animal
        fields = (
            'id', 'name', 'species', 'breed', 'breed_detail', 'age_years',
            'age_months', 'total_age_in_months', 'gender', 'size',
            'energy_level', 'good_with_cats', 'good_with_dogs',
            'good_with_children', 'requires_garden', 'max_hours_alone_per_day',
            'required_experience_level', 'is_spayed_neutered', 'is_vaccinated',
            'is_microchipped', 'microchip_code', 'special_needs',
            'health_notes', 'description', 'status', 'date_entry_shelter',
            'date_adopted', 'shelter_name', 'city', 'images',
            'created_at', 'updated_at'
        )


class AnimalCreateUpdateSerializer(serializers.ModelSerializer):
    """
    Serializzatore in scrittura per la creazione e modifica della scheda da parte del rifugio.
    """
    class Meta:
        model = Animal
        exclude = ('shelter', 'created_at', 'updated_at')

    def validate(self, attrs):
        # Se viene inserito il microchip, ne verifica l'unicità
        microchip = attrs.get('microchip_code')
        if microchip and Animal.objects.filter(microchip_code=microchip).exclude(pk=getattr(self.instance, 'pk', None)).exists():
            raise serializers.ValidationError({"microchip_code": "Questo codice microchip risulta già registrato nel sistema."})
        return attrs


class HomeVisitSerializer(serializers.ModelSerializer):
    class Meta:
        model = HomeVisit
        fields = ('id', 'evaluator_name', 'scheduled_date', 'completed_date', 'outcome', 'report_notes')


class ShelterApplicationSerializer(serializers.ModelSerializer):
    """
    Serializzatore dettagliato delle domande di adozione per la dashboard del rifugio.
    """
    adopter_detail = UserSerializer(source='adopter', read_only=True)
    animal_detail = AnimalSerializer(source='animal', read_only=True)
    home_visit = HomeVisitSerializer(read_only=True)

    class Meta:
        model = AdoptionApplication
        fields = (
            'id', 'animal', 'animal_detail', 'adopter', 'adopter_detail',
            'status', 'motivational_notes', 'compatibility_score_at_submission',
            'shelter_notes', 'home_visit', 'submitted_at', 'updated_at'
        )
        read_only_fields = ('id', 'animal', 'adopter', 'compatibility_score_at_submission', 'submitted_at')


class ApplicationStatusUpdateSerializer(serializers.ModelSerializer):
    """
    Serializzatore per l'aggiornamento dello stato della candidatura e note del rifugio.
    """
    class Meta:
        model = AdoptionApplication
        fields = ('status', 'shelter_notes')