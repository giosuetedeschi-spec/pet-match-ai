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