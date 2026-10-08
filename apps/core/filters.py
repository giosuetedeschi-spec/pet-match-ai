from math import cos, radians

import django_filters
from django.db.models import ExpressionWrapper, F, FloatField, Q, Value
from django.db.models.functions import ASin, Cast, Cos, Least, Power, Radians, Sin, Sqrt
from rest_framework.exceptions import ValidationError
from rest_framework.filters import BaseFilterBackend

from apps.core.models import Animal, AnimalEnergy, AnimalSize, Comune, Species


class AnimalFilter(django_filters.FilterSet):
    """
    Filtro avanzato per la ricerca pubblica nel catalogo animali.
    """
    species = django_filters.ChoiceFilter(choices=Species.choices)
    breed = django_filters.NumberFilter(field_name='breed__id')
    size = django_filters.MultipleChoiceFilter(choices=AnimalSize.choices)
    energy_level = django_filters.MultipleChoiceFilter(choices=AnimalEnergy.choices)
    gender = django_filters.ChoiceFilter(choices=[('M', 'Maschio'), ('F', 'Femmina')])

    # Filtri Booleani Compatibilità
    good_with_cats = django_filters.BooleanFilter()
    good_with_dogs = django_filters.BooleanFilter()
    good_with_children = django_filters.BooleanFilter()
    requires_garden = django_filters.BooleanFilter()

    # Filtri di Posizione (derivati dal Rifugio)
    city = django_filters.CharFilter(field_name='shelter__user__city', lookup_expr='icontains')
    province = django_filters.CharFilter(field_name='shelter__user__province', lookup_expr='iexact')

    # Filtri per Età (in Anni)
    min_age_years = django_filters.NumberFilter(method='filter_min_age')
    max_age_years = django_filters.NumberFilter(method='filter_max_age')

    # Ricerca Testuale Generica (Nome, Descrizione, Razza, Nome Rifugio)
    search = django_filters.CharFilter(method='filter_search')

    class Meta:
        model = Animal
        fields = [
            'species', 'breed', 'size', 'energy_level', 'gender',
            'good_with_cats', 'good_with_dogs', 'good_with_children',
            'requires_garden', 'city', 'province'
        ]

    def filter_min_age(self, queryset, name, value):
        return queryset.filter(age_years__gte=value)

    def filter_max_age(self, queryset, name, value):
        return queryset.filter(age_years__lte=value)

    def filter_search(self, queryset, name, value):
        if not value:
            return queryset
        return queryset.filter(
            Q(name__icontains=value) |
            Q(description__icontains=value) |
            Q(breed__name__icontains=value) |
            Q(shelter__shelter_name__icontains=value)
        )


class ComuneDistanceFilterBackend(BaseFilterBackend):
    """Filter catalog by straight-line distance from an ISTAT comune centroid."""
    default_radius_km = 50.0
    max_radius_km = 1500.0

    def filter_queryset(self, request, queryset, view):
        comune_code = request.query_params.get('comune')
        radius_value = request.query_params.get('radius_km')
        if not comune_code:
            if radius_value:
                raise ValidationError({'comune': 'Seleziona un comune per usare il raggio di ricerca.'})
            return queryset

        try:
            origin = Comune.objects.get(pk=comune_code)
        except Comune.DoesNotExist as exc:
            raise ValidationError({'comune': 'Codice ISTAT del comune non valido.'}) from exc

        try:
            radius_km = float(radius_value) if radius_value else self.default_radius_km
        except (TypeError, ValueError) as exc:
            raise ValidationError({'radius_km': 'Inserisci un raggio numerico valido.'}) from exc
        if not 0 < radius_km <= self.max_radius_km:
            raise ValidationError({
                'radius_km': (
                    'Il raggio deve essere maggiore di 0 e non superiore a '
                    f'{self.max_radius_km:g} km.'
                )
            })

        latitude = float(origin.latitude)
        longitude = float(origin.longitude)
        latitude_delta = radius_km / 111.32
        edge_latitude = min(89.9, abs(latitude) + latitude_delta)
        longitude_delta = radius_km / (111.32 * max(abs(cos(radians(edge_latitude))), 0.01))
        queryset = queryset.filter(
            shelter__user__comune__latitude__gte=max(-90, latitude - latitude_delta),
            shelter__user__comune__latitude__lte=min(90, latitude + latitude_delta),
        )
        if longitude_delta < 180:
            queryset = queryset.filter(
                shelter__user__comune__longitude__gte=longitude - longitude_delta,
                shelter__user__comune__longitude__lte=longitude + longitude_delta,
            )

        shelter_latitude = Cast(F('shelter__user__comune__latitude'), FloatField())
        shelter_longitude = Cast(F('shelter__user__comune__longitude'), FloatField())
        lat_delta = Radians(shelter_latitude - Value(latitude))
        lon_delta = Radians(shelter_longitude - Value(longitude))
        haversine = (
            Power(Sin(lat_delta / Value(2.0)), Value(2.0))
            + Cos(Radians(Value(latitude)))
            * Cos(Radians(shelter_latitude))
            * Power(Sin(lon_delta / Value(2.0)), Value(2.0))
        )
        queryset = queryset.annotate(
            distance_km=ExpressionWrapper(
                Value(12742.0) * ASin(Sqrt(Least(haversine, Value(1.0)))),
                output_field=FloatField(),
            )
        ).filter(distance_km__lte=radius_km)
        return queryset.order_by('distance_km', '-created_at')
