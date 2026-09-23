import django_filters
from django.db.models import Q, F
from apps.core.models import Animal, Species, AnimalSize, AnimalEnergy, AnimalStatus


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