from django.views.generic import TemplateView

class HomeView(TemplateView):
    template_name = 'core/home.html'


from rest_framework import generics, status, permissions, parsers
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404

from apps.core.models import Animal, AnimalImage
from apps.core.serializers import AnimalImageSerializer, BulkImageUploadSerializer
from apps.core.permissions import IsShelterOwnerOfAnimal


class AnimalImageUploadView(APIView):
    """
    Endpoint per caricare una o più immagini per uno specifico animale.
    Supporta multipart/form-data.
    """
    permission_classes = (IsShelterOwnerOfAnimal,)
    parser_classes = (parsers.MultiPartParser, parsers.FormParser)

    def post(self, request, animal_id):
        animal = get_object_or_404(Animal, id=animal_id)
        self.check_object_permissions(request, animal)

        serializer = BulkImageUploadSerializer(data=request.data)
        if serializer.is_valid():
            uploaded_images = serializer.validated_data['images']
            created_instances = []

            for index, img_file in enumerate(uploaded_images):
                # La prima foto caricata diventa copertina se non ne esistono altre
                is_first = (animal.images.count() == 0 and index == 0)
                
                img_instance = AnimalImage.objects.create(
                    animal=animal,
                    image=img_file,
                    is_primary=is_first,
                    order=animal.images.count() + 1
                )
                created_instances.append(img_instance)

            return Response(
                AnimalImageSerializer(created_instances, many=True).data,
                status=status.HTTP_201_CREATED
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AnimalImageDetailView(generics.RetrieveDestroyAPIView):
    """
    Endpoint per consultare o eliminare una singola immagine.
    """
    queryset = AnimalImage.objects.all()
    serializer_class = AnimalImageSerializer
    permission_classes = (IsShelterOwnerOfAnimal,)


class SetPrimaryImageView(APIView):
    """
    Endpoint per impostare un'immagine come foto principale di copertina.
    """
    permission_classes = (IsShelterOwnerOfAnimal,)

    def patch(self, request, pk):
        image = get_object_or_404(AnimalImage, pk=pk)
        self.check_object_permissions(request, image)

        image.is_primary = True
        image.save()

        return Response(
            {"detail": f"Immagine #{image.id} impostata come foto di copertina per {image.animal.name}."},
            status=status.HTTP_200_OK
        )

from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.db.models import Count, Avg, Q

from apps.core.models import (
    Animal, AdoptionApplication, ApplicationStatus,
    HomeVisit, AnimalStatus
)
from apps.core.serializers import (
    AnimalSerializer,
    AnimalCreateUpdateSerializer,
    ShelterApplicationSerializer,
    ApplicationStatusUpdateSerializer,
    HomeVisitSerializer
)
from apps.core.permissions import IsShelterOwnerOfAnimal


class IsShelterUser(permissions.BasePermission):
    """
    Permesso base che verifica che l'utente sia autenticato e abbia il ruolo SHELTER.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'SHELTER' and hasattr(request.user, 'shelter_profile')


class ShelterAnimalListCreateAPIView(generics.ListCreateAPIView):
    """
    GET: Elenco degli animali registrati dal rifugio loggato.
    POST: Creazione di una nuova scheda animale.
    """
    permission_classes = (IsShelterUser,)

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return AnimalCreateUpdateSerializer
        return AnimalSerializer

    def get_queryset(self):
        return Animal.objects.filter(shelter=self.request.user.shelter_profile).select_related(
            'breed', 'shelter', 'shelter__user'
        ).prefetch_related('images')

    def perform_create(self, serializer):
        serializer.save(shelter=self.request.user.shelter_profile)


class ShelterAnimalDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET / PUT / PATCH / DELETE: Gestione della singola scheda animale.
    """
    permission_classes = (IsShelterOwnerOfAnimal,)

    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return AnimalCreateUpdateSerializer
        return AnimalSerializer

    def get_queryset(self):
        return Animal.objects.filter(shelter=self.request.user.shelter_profile)


class ShelterApplicationListAPIView(generics.ListAPIView):
    """
    Elenco delle candidature di adozione ricevute per gli animali del rifugio loggato.
    Supporta filtri per stato e ID animale (`?status=SUBMITTED` o `?animal_id=1`).
    """
    serializer_class = ShelterApplicationSerializer
    permission_classes = (IsShelterUser,)

    def get_queryset(self):
        queryset = AdoptionApplication.objects.filter(
            animal__shelter=self.request.user.shelter_profile
        ).select_related(
            'adopter', 'adopter__adopter_profile',
            'animal', 'animal__breed', 'home_visit'
        )

        app_status = self.request.query_params.get('status')
        animal_id = self.request.query_params.get('animal_id')

        if app_status:
            queryset = queryset.filter(status=app_status)
        if animal_id:
            queryset = queryset.filter(animal_id=animal_id)

        return queryset


class ShelterApplicationDetailAPIView(generics.RetrieveUpdateAPIView):
    """
    Dettaglio e aggiornamento stato/note di una domanda di adozione ricevuta.
    """
    permission_classes = (IsShelterUser,)

    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return ApplicationStatusUpdateSerializer
        return ShelterApplicationSerializer

    def get_queryset(self):
        return AdoptionApplication.objects.filter(
            animal__shelter=self.request.user.shelter_profile
        )

    def perform_update(self, serializer):
        application = serializer.save()
        # Se lo stato passa ad ADOPTED, la scheda dell'animale viene aggiornata in ADOPTED
        if application.status == ApplicationStatus.APPROVED:
            animal = application.animal
            animal.status = AnimalStatus.ADOPTED
            animal.save()


class ScheduleHomeVisitAPIView(APIView):
    """
    Pianifica o aggiorna la visita pre-affido per una candidatura.
    """
    permission_classes = (IsShelterUser,)

    def post(self, request, application_id):
        application = get_object_or_404(
            AdoptionApplication,
            id=application_id,
            animal__shelter=request.user.shelter_profile
        )

        serializer = HomeVisitSerializer(data=request.data)
        if serializer.is_valid():
            visit, created = HomeVisit.objects.update_or_create(
                application=application,
                defaults=serializer.validated_data
            )
            # Aggiorna lo stato della candidatura
            application.status = ApplicationStatus.HOME_VISIT
            application.save()

            return Response(HomeVisitSerializer(visit).data, status=status.HTTP_200_OK if not created else status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ShelterDashboardStatsAPIView(APIView):
    """
    Restituisce i dati analitici sintetici per la dashboard del rifugio.
    """
    permission_classes = (IsShelterUser,)

    def get(self, request):
        shelter = request.user.shelter_profile
        animals = Animal.objects.filter(shelter=shelter)
        applications = AdoptionApplication.objects.filter(animal__shelter=shelter)

        # Statistiche Animali
        total_animals = animals.count()
        available_animals = animals.filter(status=AnimalStatus.AVAILABLE).count()
        adopted_animals = animals.filter(status=AnimalStatus.ADOPTED).count()

        # Statistiche Candidature
        total_applications = applications.count()
        pending_applications = applications.filter(status__in=[ApplicationStatus.SUBMITTED, ApplicationStatus.IN_REVIEW]).count()
        scheduled_visits = applications.filter(status=ApplicationStatus.HOME_VISIT).count()

        # Metrica ML sul tempo stimato di adozione medio (dalla tabella MatchResult)
        from apps.matching.models import MatchResult
        avg_predicted_days = MatchResult.objects.filter(
            animal__shelter=shelter,
            animal__status=AnimalStatus.AVAILABLE
        ).aggregate(Avg('predicted_adoption_time_days'))['predicted_adoption_time_days__avg']

        data = {
            'shelter_name': shelter.shelter_name,
            'is_verified': shelter.is_verified,
            'animals_summary': {
                'total': total_animals,
                'available': available_animals,
                'adopted': adopted_animals,
            },
            'applications_summary': {
                'total': total_applications,
                'pending_evaluation': pending_applications,
                'home_visits_scheduled': scheduled_visits,
            },
            'ml_analytics': {
                'avg_predicted_adoption_time_days': round(avg_predicted_days, 1) if avg_predicted_days else None
            }
        }

        return Response(data, status=status.HTTP_200_OK)


from rest_framework import generics, permissions, filters
from rest_framework.pagination import PageNumberPagination
from django_filters.rest_framework import DjangoFilterBackend

from apps.core.models import Animal, AnimalStatus
from apps.core.filters import AnimalFilter
from apps.core.serializers import (
    PublicAnimalListSerializer,
    PublicAnimalDetailSerializer
)


class CatalogPagination(PageNumberPagination):
    page_size = 12
    page_size_query_param = 'page_size'
    max_page_size = 48


class PublicAnimalCatalogAPIView(generics.ListAPIView):
    """
    API Pubblica: Esplora il catalogo degli animali disponibili per l'adozione.
    Supporta: Filtri avanzati, Ricerca testuale, Ordinamento e Paginazione.
    """
    permission_classes = (permissions.AllowAny,)
    serializer_class = PublicAnimalListSerializer
    pagination_class = CatalogPagination
    filter_backends = (DjangoFilterBackend, filters.OrderingFilter)
    filterset_class = AnimalFilter
    ordering_fields = ['created_at', 'age_years', 'name']
    ordering = ['-created_at']

    def get_queryset(self):
        return Animal.objects.filter(
            status=AnimalStatus.AVAILABLE
        ).select_related(
            'breed', 'shelter', 'shelter__user'
        ).prefetch_related('images')


class PublicAnimalDetailAPIView(generics.RetrieveAPIView):
    """
    API Pubblica: Dettaglio completo di una singola scheda animale.
    """
    permission_classes = (permissions.AllowAny,)
    serializer_class = PublicAnimalDetailSerializer

    def get_queryset(self):
        return Animal.objects.filter(
            status=AnimalStatus.AVAILABLE
        ).select_related(
            'breed', 'shelter', 'shelter__user'
        ).prefetch_related('images')

from rest_framework import status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from apps.core.models import Animal, AnimalStatus, AdoptionApplication, ApplicationStatus
from apps.core.serializers import AdoptionApplicationCreateSerializer, ShelterApplicationSerializer
from apps.core.permissions import IsAdopterUser
from apps.matching.services import MatchingService


class AdoptionApplicationCreateAPIView(APIView):
    """
    API per l'inoltro di una domanda di adozione per uno specifico animale.
    """
    permission_classes = (IsAdopterUser,)

    def post(self, request, animal_id):
        animal = get_object_or_404(Animal, id=animal_id)

        # 1. Verifica disponibilità dell'animale
        if animal.status != AnimalStatus.AVAILABLE:
            return Response(
                {"detail": "Questo animale non è al momento disponibile per l'adozione."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 2. Verifica candidatura duplicata
        if AdoptionApplication.objects.filter(adopter=request.user, animal=animal).exists():
            return Response(
                {"detail": "Hai già inviato una candidatura per questo animale."},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = AdoptionApplicationCreateSerializer(data=request.data)
        if serializer.is_valid():
            # 3. Calcolo o recupero dello score ML di compatibilità all'atto dell'invio
            match_record = MatchingService.process_and_save_match(request.user, animal)
            score_at_submission = match_record.overall_score if match_record else 0.0

            # 4. Creazione e salvataggio della domanda
            application = serializer.save(
                adopter=request.user,
                animal=animal,
                status=ApplicationStatus.SUBMITTED,
                compatibility_score_at_submission=score_at_submission
            )

            # Ritorna la candidatura creata con il dettaglio completo
            response_serializer = ShelterApplicationSerializer(application, context={'request': request})
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



from rest_framework import generics, status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from apps.core.models import AdoptionApplication, ApplicationStatus
from apps.core.serializers import (
    AdopterApplicationListSerializer,
    AdopterApplicationDetailSerializer
)
from apps.core.permissions import IsAdopterUser


class AdopterApplicationListAPIView(generics.ListAPIView):
    """
    API: Elenco delle candidature inviate dall'adottante loggato.
    Supporta filtri per stato (`?status=IN_REVIEW`).
    """
    permission_classes = (IsAdopterUser,)
    serializer_class = AdopterApplicationListSerializer

    def get_queryset(self):
        queryset = AdoptionApplication.objects.filter(
            adopter=self.request.user
        ).select_related(
            'animal', 'animal__breed', 'animal__shelter', 'animal__shelter__user'
        ).prefetch_related('animal__images')

        status_param = self.request.query_params.get('status')
        if status_param:
            queryset = queryset.filter(status=status_param)

        return queryset


class AdopterApplicationDetailAPIView(generics.RetrieveAPIView):
    """
    API: Dettaglio della singola candidatura dell'adottante.
    """
    permission_classes = (IsAdopterUser,)
    serializer_class = AdopterApplicationDetailSerializer

    def get_queryset(self):
        return AdoptionApplication.objects.filter(
            adopter=self.request.user
        ).select_related(
            'animal', 'animal__shelter', 'animal__shelter__user', 'home_visit'
        )


class AdopterApplicationWithdrawAPIView(APIView):
    """
    API: Permette all'adottante di ritirare spontaneamente una domanda di adozione.
    """
    permission_classes = (IsAdopterUser,)

    def patch(self, request, pk):
        application = get_object_or_404(
            AdoptionApplication,
            id=pk,
            adopter=request.user
        )

        # Impossibile ritirare pratiche già archiviate o concluse
        if application.status in [ApplicationStatus.APPROVED, ApplicationStatus.REJECTED, ApplicationStatus.WITHDRAWN]:
            return Response(
                {"detail": f"Impossibile ritirare una candidatura nello stato '{application.get_status_display()}'."},
                status=status.HTTP_400_BAD_REQUEST
            )

        application.status = ApplicationStatus.WITHDRAWN
        application.save()

        return Response(
            {"detail": "La tua candidatura è stata ritirata con successo."},
            status=status.HTTP_200_OK
        )


from rest_framework import generics, status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from apps.core.models import AdoptionApplication, ApplicationStatus
from apps.core.serializers import (
    AdopterApplicationListSerializer,
    AdopterApplicationDetailSerializer
)
from apps.core.permissions import IsAdopterUser


class AdopterApplicationListAPIView(generics.ListAPIView):
    """
    API: Restituisce l'elenco delle candidature d'adozione inviate dall'utente.
    Permette di filtrare per stato tramite query parameter:
    ?status=SUBMITTED (Inviata)
    ?status=IN_REVIEW (In Valutazione)
    ?status=HOME_VISIT (Visita Programmata)
    ?status=APPROVED (Approvata)
    ?status=REJECTED (Rifiutata)
    """
    permission_classes = (IsAdopterUser,)
    serializer_class = AdopterApplicationListSerializer

    def get_queryset(self):
        queryset = AdoptionApplication.objects.filter(
            adopter=self.request.user
        ).select_related(
            'animal', 'animal__breed', 'animal__shelter', 'animal__shelter__user'
        ).prefetch_related('animal__images')

        status_param = self.request.query_params.get('status')
        if status_param:
            queryset = queryset.filter(status=status_param)

        return queryset


class AdopterApplicationDetailAPIView(generics.RetrieveAPIView):
    """
    API: Dettaglio di una singola candidatura d'adozione per l'adottante.
    """
    permission_classes = (IsAdopterUser,)
    serializer_class = AdopterApplicationDetailSerializer

    def get_queryset(self):
        return AdoptionApplication.objects.filter(
            adopter=self.request.user
        ).select_related(
            'animal', 'animal__shelter', 'animal__shelter__user', 'home_visit'
        )


class AdopterApplicationWithdrawAPIView(APIView):
    """
    API: Consente all'adottante di ritirare spontaneamente la propria candidatura
    finché non è stata conclusa o rifiutata definitivamente.
    """
    permission_classes = (IsAdopterUser,)

    def patch(self, request, pk):
        application = get_object_or_404(
            AdoptionApplication,
            id=pk,
            adopter=request.user
        )

        if application.status in [ApplicationStatus.APPROVED, ApplicationStatus.REJECTED, ApplicationStatus.WITHDRAWN]:
            return Response(
                {"detail": f"Impossibile ritirare una candidatura nello stato '{application.get_status_display()}'."},
                status=status.HTTP_400_BAD_REQUEST
            )

        application.status = ApplicationStatus.WITHDRAWN
        application.save()

        return Response(
            {"detail": "La tua candidatura è stata ritirata con successo."},
            status=status.HTTP_200_OK
        )