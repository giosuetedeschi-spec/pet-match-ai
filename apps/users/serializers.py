from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.utils import timezone
from apps.users.models import AdopterProfile, ShelterProfile
from apps.audit.models import GDPRConsentLog, ConsentType

User = get_user_model()


class AdopterProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = AdopterProfile
        exclude = ('user',)


class ShelterProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShelterProfile
        exclude = ('user',)


class UserSerializer(serializers.ModelSerializer):
    adopter_profile = AdopterProfileSerializer(read_only=True)
    shelter_profile = ShelterProfileSerializer(read_only=True)

    class Meta:
        model = User
        fields = (
            'id', 'username', 'email', 'first_name', 'last_name',
            'role', 'phone_number', 'address', 'city', 'province',
            'postal_code', 'avatar', 'gdpr_consent', 'gdpr_consent_date',
            'marketing_consent', 'adopter_profile', 'shelter_profile'
        )
        read_only_fields = ('id', 'gdpr_consent', 'gdpr_consent_date')


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)
    gdpr_consent = serializers.BooleanField(required=True)

    class Meta:
        model = User
        fields = (
            'username', 'email', 'password', 'password_confirm',
            'first_name', 'last_name', 'role', 'phone_number',
            'gdpr_consent', 'marketing_consent'
        )

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({"password": "Le password non coincidono."})
        if not attrs.get('gdpr_consent'):
            raise serializers.ValidationError({"gdpr_consent": "Il consenso GDPR è obbligatorio per registrarsi."})
        return attrs

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        gdpr_granted = validated_data.get('gdpr_consent')
        
        if gdpr_granted:
            validated_data['gdpr_consent_date'] = timezone.now()

        password = validated_data.pop('password')
        user = User.objects.create(**validated_data)
        user.set_password(password)
        user.save()

        # Creazione automatica del profilo in base al ruolo
        if user.role == User.Role.ADOPTER:
            AdopterProfile.objects.create(user=user)
        elif user.role == User.Role.SHELTER:
            ShelterProfile.objects.create(
                user=user,
                shelter_name=f"Rifugio {user.username}",
                official_email=user.email
            )

        # Tracciamento Audit Log GDPR
        request = self.context.get('request')
        ip_addr = request.META.get('REMOTE_ADDR') if request else None
        user_agent = request.META.get('HTTP_USER_AGENT', '') if request else ''

        GDPRConsentLog.objects.create(
            user=user,
            consent_type=ConsentType.PRIVACY,
            granted=True,
            ip_address=ip_addr,
            user_agent=user_agent
        )

        return user


class GDPRConsentUpdateSerializer(serializers.Serializer):
    consent_type = serializers.ChoiceField(choices=ConsentType.choices)
    granted = serializers.BooleanField()



from rest_framework import serializers


class AccountDeletionSerializer(serializers.Serializer):
    """
    Serializzatore per la conferma di sicurezza dell'eliminazione account.
    Richiede la password attuale e una conferma esplicita.
    """
    password = serializers.CharField(write_only=True, required=True)
    confirm_deletion = serializers.BooleanField(required=True)

    def validate_confirm_deletion(self, value):
        if not value:
            raise serializers.ValidationError("È necessario confermare la volontà di eliminare l'account.")
        return value

    def validate(self, attrs):
        user = self.context['request'].user
        if not user.check_password(attrs['password']):
            raise serializers.ValidationError({"password": "La password inserita non è corretta."})
        return attrs