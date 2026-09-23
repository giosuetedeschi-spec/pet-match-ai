from rest_framework import views, permissions, status
from rest_framework.response import Response
from apps.matching.services import MatchingService
from apps.matching.models import MatchResult
from rest_framework import serializers


class MatchResultSerializer(serializers.ModelSerializer):
    animal_name = serializers.CharField(source='animal.name', read_only=True)
    animal_species = serializers.CharField(source='animal.species', read_only=True)
    shelter_name = serializers.CharField(source='animal.shelter.shelter_name', read_only=True)

    class Meta:
        model = MatchResult
        fields = (
            'animal', 'animal_name', 'animal_species', 'shelter_name',
            'overall_score', 'score_breakdown',
            'predicted_adoption_time_days', 'survival_probability_30d'
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