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

