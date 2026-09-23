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


from rest_framework import serializers
from apps.core.models import Animal, AnimalImage
from apps.matching.models import MatchResult


class PublicAnimalImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnimalImage
        fields = ('id', 'image', 'caption', 'is_primary', 'order')


class PublicAnimalListSerializer(serializers.ModelSerializer):
    """
    Serializzatore leggero per la griglia del catalogo pubblico.
    """
    species_display = serializers.CharField(source='get_species_display', read_only=True)
    size_display = serializers.CharField(source='get_size_display', read_only=True)
    gender_display = serializers.CharField(source='get_gender_display', read_only=True)
    breed_name = serializers.CharField(source='breed.name', read_only=True, default="Meticcio")
    shelter_name = serializers.CharField(source='shelter.shelter_name', read_only=True)
    city = serializers.CharField(source='shelter.user.city', read_only=True)
    province = serializers.CharField(source='shelter.user.province', read_only=True)
    primary_image = serializers.SerializerMethodField()
    match_score = serializers.SerializerMethodField()

    class Meta:
        model = Animal
        fields = (
            'id', 'name', 'species', 'species_display', 'breed_name',
            'age_years', 'age_months', 'gender', 'gender_display',
            'size', 'size_display', 'energy_level', 'city', 'province',
            'shelter_name', 'primary_image', 'match_score', 'created_at'
        )

    def get_primary_image(self, obj):
        primary = obj.images.filter(is_primary=True).first() or obj.images.first()
        if primary and primary.image:
            request = self.context.get('request')
            return request.build_absolute_uri(primary.image.url) if request else primary.image.url
        return None

    def get_match_score(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated and request.user.role == 'ADOPTER':
            match_res = MatchResult.objects.filter(adopter=request.user, animal=obj).first()
            return round(match_res.overall_score, 1) if match_res else None
        return None


class PublicAnimalDetailSerializer(serializers.ModelSerializer):
    """
    Serializzatore completo per la scheda di dettaglio dell'animale.
    """
    species_display = serializers.CharField(source='get_species_display', read_only=True)
    size_display = serializers.CharField(source='get_size_display', read_only=True)
    energy_level_display = serializers.CharField(source='get_energy_level_display', read_only=True)
    gender_display = serializers.CharField(source='get_gender_display', read_only=True)
    breed_name = serializers.CharField(source='breed.name', read_only=True, default="Meticcio")
    images = PublicAnimalImageSerializer(many=True, read_only=True)
    
    shelter_info = serializers.SerializerMethodField()
    match_data = serializers.SerializerMethodField()

    class Meta:
        model = Animal
        fields = (
            'id', 'name', 'species', 'species_display', 'breed_name',
            'age_years', 'age_months', 'gender', 'gender_display',
            'size', 'size_display', 'energy_level', 'energy_level_display',
            'good_with_cats', 'good_with_dogs', 'good_with_children',
            'requires_garden', 'max_hours_alone_per_day', 'required_experience_level',
            'is_spayed_neutered', 'is_vaccinated', 'special_needs',
            'description', 'status', 'shelter_info', 'images', 'match_data',
            'created_at'
        )

    def get_shelter_info(self, obj):
        shelter = obj.shelter
        return {
            'id': shelter.id,
            'shelter_name': shelter.shelter_name,
            'city': shelter.user.city,
            'province': shelter.user.province,
            'official_email': shelter.official_email,
            'is_verified': shelter.is_verified
        }

    def get_match_data(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated and request.user.role == 'ADOPTER':
            match_res = MatchResult.objects.filter(adopter=request.user, animal=obj).first()
            if match_res:
                return {
                    'overall_score': round(match_res.overall_score, 1),
                    'score_breakdown': match_res.score_breakdown,
                    'predicted_adoption_time_days': match_res.predicted_adoption_time_days
                }
        return None


from rest_framework import serializers
from apps.core.models import AdoptionApplication, ApplicationStatus


class AdoptionApplicationCreateSerializer(serializers.ModelSerializer):
    """
    Serializzatore per l'invio di una nuova candidatura di adozione da parte dell'adottante.
    """
    class Meta:
        model = AdoptionApplication
        fields = ('id', 'motivational_notes', 'submitted_at')
        read_only_fields = ('id', 'submitted_at')

    def validate_motivational_notes(self, value):
        text = value.strip()
        if len(text) < 50:
            raise serializers.ValidationError("La lettera motivazionale deve contenere almeno 50 caratteri spiegando le tue motivazioni.")
        return text


from rest_framework import serializers
from apps.core.models import AdoptionApplication, ApplicationStatus, HomeVisit
from apps.core.serializers import PublicAnimalListSerializer, HomeVisitSerializer


class AdopterApplicationListSerializer(serializers.ModelSerializer):
    """
    Serializzatore sintetico per l'elenco delle candidature inviate dall'utente.
    """
    animal_detail = PublicAnimalListSerializer(source='animal', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    shelter_name = serializers.CharField(source='animal.shelter.shelter_name', read_only=True)

    class Meta:
        model = AdoptionApplication
        fields = (
            'id', 'animal', 'animal_detail', 'shelter_name', 'status',
            'status_display', 'compatibility_score_at_submission',
            'submitted_at', 'updated_at'
        )


class AdopterApplicationDetailSerializer(serializers.ModelSerializer):
    """
    Serializzatore di dettaglio della domanda con info rifugio e visita pre-affido.
    """
    animal_detail = PublicAnimalListSerializer(source='animal', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    home_visit = HomeVisitSerializer(read_only=True)
    shelter_contact = serializers.SerializerMethodField()

    class Meta:
        model = AdoptionApplication
        fields = (
            'id', 'animal', 'animal_detail', 'shelter_contact', 'status',
            'status_display', 'motivational_notes', 'compatibility_score_at_submission',
            'shelter_notes', 'home_visit', 'submitted_at', 'updated_at'
        )

    def get_shelter_contact(self, obj):
        shelter = obj.animal.shelter
        return {
            'shelter_name': shelter.shelter_name,
            'official_email': shelter.official_email,
            'city': shelter.user.city,
            'province': shelter.user.province,
            'phone_number': shelter.user.phone_number
        }



from rest_framework import serializers
from apps.core.models import AdoptionApplication, ApplicationStatus, HomeVisit
from apps.core.serializers import PublicAnimalListSerializer, HomeVisitSerializer


class AdopterApplicationListSerializer(serializers.ModelSerializer):
    """
    Serializzatore sintetico per l'elenco delle domande inviate dall'adottante.
    """
    animal_detail = PublicAnimalListSerializer(source='animal', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    shelter_name = serializers.CharField(source='animal.shelter.shelter_name', read_only=True)

    class Meta:
        model = AdoptionApplication
        fields = (
            'id', 
            'animal', 
            'animal_detail', 
            'shelter_name', 
            'status',
            'status_display', 
            'compatibility_score_at_submission',
            'submitted_at', 
            'updated_at'
        )


class AdopterApplicationDetailSerializer(serializers.ModelSerializer):
    """
    Serializzatore dettagliato della domanda con informazioni di contatto del rifugio
    e dettagli sulla visita pre-affido (se programmata).
    """
    animal_detail = PublicAnimalListSerializer(source='animal', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    home_visit = HomeVisitSerializer(read_only=True)
    shelter_contact = serializers.SerializerMethodField()

    class Meta:
        model = AdoptionApplication
        fields = (
            'id', 
            'animal', 
            'animal_detail', 
            'shelter_contact', 
            'status',
            'status_display', 
            'motivational_notes', 
            'compatibility_score_at_submission',
            'shelter_notes', 
            'home_visit', 
            'submitted_at', 
            'updated_at'
        )

    def get_shelter_contact(self, obj):
        shelter = obj.animal.shelter
        return {
            'shelter_name': shelter.shelter_name,
            'official_email': shelter.official_email,
            'city': shelter.user.city,
            'province': shelter.user.province,
            'phone_number': shelter.user.phone_number
        }