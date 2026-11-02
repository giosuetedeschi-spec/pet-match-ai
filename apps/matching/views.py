from rest_framework import permissions, serializers, status, views
from rest_framework.response import Response
from django.utils import timezone

from apps.core.models import Animal, AnimalStatus
from apps.users.models import AdopterProfile
from apps.matching.services import MatchingService
from apps.matching.models import MatchResult


class MatchResultSerializer(serializers.ModelSerializer):
    animal_name = serializers.CharField(source='animal.name', read_only=True)
    animal_species = serializers.CharField(source='animal.species', read_only=True)
    shelter_name = serializers.CharField(source='animal.shelter.shelter_name', read_only=True)

    class Meta:
        model = MatchResult
        fields = (
            'animal', 'animal_name', 'animal_species', 'shelter_name',
            'overall_score', 'score_breakdown'
        )


class AdopterRecommendationsAPIView(views.APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request):
        if request.user.role != 'ADOPTER':
            return Response(
                {"detail": "Soltanto gli utenti adottanti possono richiedere raccomandazioni."},
                status=status.HTTP_403_FORBIDDEN
            )

        limit = int(request.query_params.get('limit', 10))
        top_matches = MatchingService.get_top_matches_for_adopter(request.user, limit=limit)
        serializer = MatchResultSerializer(top_matches, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)


class MatchingPreviewSerializer(serializers.Serializer):
    housing_type = serializers.ChoiceField(choices=AdopterProfile.HousingType.choices)
    garden_sqm = serializers.IntegerField(min_value=0, max_value=10000)
    has_children = serializers.BooleanField()
    has_other_pets = serializers.BooleanField(required=False, default=False)
    has_dogs = serializers.BooleanField(required=False, default=False)
    has_cats = serializers.BooleanField(required=False, default=False)
    hours_away_from_home = serializers.IntegerField(min_value=0, max_value=24)
    activity_level = serializers.ChoiceField(choices=AdopterProfile.ActivityLevel.choices)
    experience_level = serializers.ChoiceField(choices=AdopterProfile.ExperienceLevel.choices)
    preferred_species = serializers.ChoiceField(choices=(('ANY', 'Qualsiasi'), *Animal._meta.get_field('species').choices))
    preferred_age_min_months = serializers.IntegerField(min_value=0, max_value=1200)
    preferred_age_max_months = serializers.IntegerField(min_value=0, max_value=1200)

    def validate(self, attrs):
        if attrs['preferred_age_min_months'] > attrs['preferred_age_max_months']:
            raise serializers.ValidationError({'preferred_age_max_months': 'L’età massima deve essere maggiore o uguale a quella minima.'})
        return attrs


class MatchingPreviewAPIView(views.APIView):
    """Anonymous demo ranking using the current, deterministic Django compatibility rules."""
    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        serializer = MatchingPreviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        answers = serializer.validated_data
        profile = AdopterProfile(**answers)
        animals = Animal.objects.filter(
            status=AnimalStatus.AVAILABLE,
            shelter__is_verified=True,
        ).select_related('breed', 'shelter', 'shelter__user').order_by('name')
        if answers['preferred_species'] != 'ANY':
            animals = animals.filter(species=answers['preferred_species'])

        results = []
        excluded = []
        for animal in animals:
            age_months = animal.total_age_in_months
            if not answers['preferred_age_min_months'] <= age_months <= answers['preferred_age_max_months']:
                continue
            score, breakdown = MatchingService.calculate_match_score(profile, animal)
            if breakdown['excluded']:
                excluded.append({'name': animal.name, 'reasons': breakdown['exclusions']})
                continue
            days_in_care = max(0, (timezone.localdate() - animal.date_entry_shelter).days)
            results.append({
                'animal_id': animal.id,
                'name': animal.name,
                'species': animal.species,
                'breed': animal.breed.name if animal.breed else 'Meticcio',
                'age_months': age_months,
                'gender': animal.gender,
                'is_spayed_neutered': animal.is_spayed_neutered,
                'days_in_care': days_in_care,
                'age_months_at_intake': max(0, round(age_months - days_in_care / 30.4375)),
                'shelter': animal.shelter.shelter_name,
                'city': animal.shelter.user.city,
                'score': round(score, 1),
                'breakdown': breakdown,
                'cautions': breakdown['cautions'],
            })

        results.sort(key=lambda item: (-item['score'], item['name'].casefold()))
        return Response({
            'engine': 'deterministic-rules',
            'validated_ml': False,
            'results': results[:20],
            'total': len(results),
            'excluded_total': len(excluded),
            'excluded': excluded[:20],
        })
