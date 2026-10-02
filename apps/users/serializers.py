from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db import transaction
from apps.users.models import AdopterProfile, ShelterProfile
from apps.audit.models import GDPRConsentLog, ConsentType
from apps.core.models import Comune

User = get_user_model()


class AdopterProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = AdopterProfile
        exclude = ('user',)


class ShelterProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShelterProfile
        exclude = ('user', 'is_verified', 'verification_date', 'verification_status', 'rejection_reason')


class UserSerializer(serializers.ModelSerializer):
    adopter_profile = AdopterProfileSerializer(read_only=True)
    shelter_profile = ShelterProfileSerializer(read_only=True)
    comune = serializers.PrimaryKeyRelatedField(queryset=Comune.objects.all(), allow_null=True, required=False)
    city = serializers.CharField(read_only=True)
    province = serializers.CharField(read_only=True)

    class Meta:
        model = User
        fields = (
            'id', 'username', 'email', 'first_name', 'last_name',
            'role', 'phone_number', 'address', 'comune', 'city', 'province',
            'postal_code', 'avatar', 'gdpr_consent', 'gdpr_consent_date',
            'marketing_consent', 'adopter_profile', 'shelter_profile'
        )
        read_only_fields = ('id', 'role', 'gdpr_consent', 'gdpr_consent_date')


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    shelter_name = serializers.CharField(required=False, max_length=255)
    legal_name = serializers.CharField(required=False, max_length=255)
    organization_type = serializers.ChoiceField(choices=ShelterProfile.OrganizationType.choices, required=False)
    tax_code_vat = serializers.CharField(required=False, max_length=30)
    official_email = serializers.EmailField(required=False)
    address = serializers.CharField(required=False, max_length=255)
    comune = serializers.PrimaryKeyRelatedField(queryset=Comune.objects.all(), required=False)
    city = serializers.CharField(required=False, max_length=100)
    province = serializers.CharField(required=False, max_length=10)
    postal_code = serializers.CharField(required=False, max_length=10)
    phone_number = serializers.CharField(required=False, max_length=20)
    description = serializers.CharField(required=False, allow_blank=True)
    password_confirm = serializers.CharField(write_only=True)
    gdpr_consent = serializers.BooleanField(required=True)

    class Meta:
        model = User
        fields = (
            'username', 'email', 'password', 'password_confirm',
            'first_name', 'last_name', 'role', 'phone_number',
            'gdpr_consent', 'marketing_consent', 'shelter_name', 'legal_name',
            'organization_type', 'tax_code_vat', 'official_email', 'address', 'comune', 'city',
            'province', 'postal_code', 'description'
        )

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({"password": "Le password non coincidono."})
        if not attrs.get('gdpr_consent'):
            raise serializers.ValidationError({"gdpr_consent": "Il consenso GDPR è obbligatorio per registrarsi."})
        if attrs.get('role') == User.Role.ADMIN:
            raise serializers.ValidationError({"role": "Il ruolo amministratore non è disponibile tramite registrazione pubblica."})
        if attrs.get('role') == User.Role.SHELTER:
            required = (
                'shelter_name', 'legal_name', 'organization_type', 'tax_code_vat',
                'official_email', 'address', 'comune', 'postal_code', 'phone_number', 'description'
            )
            missing = [
                field for field in required
                if not str(attrs.get(field, '')).strip()
            ]
            if missing:
                raise serializers.ValidationError({field: "Campo obbligatorio per registrare un rifugio." for field in missing})
        return attrs

    def create(self, validated_data):
        with transaction.atomic():
            return self._create_user(validated_data)

    def _create_user(self, validated_data):
        validated_data.pop('password_confirm')
        comune = validated_data.get('comune')
        if comune:
            validated_data['city'] = comune.name
            validated_data['province'] = comune.province_abbreviation
        shelter_fields = {
            'shelter_name', 'legal_name', 'organization_type', 'tax_code_vat',
            'official_email', 'description'
        }
        shelter_data = {field: validated_data.pop(field) for field in shelter_fields if field in validated_data}
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
                **shelter_data,
                verification_status=ShelterProfile.VerificationStatus.PENDING,
                is_verified=False,
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


class ShelterRegistrationQueueSerializer(serializers.ModelSerializer):
    address = serializers.CharField(source='user.address', read_only=True)
    city = serializers.CharField(source='user.city', read_only=True)
    province = serializers.CharField(source='user.province', read_only=True)
    postal_code = serializers.CharField(source='user.postal_code', read_only=True)
    phone_number = serializers.CharField(source='user.phone_number', read_only=True)
    registrant_email = serializers.EmailField(source='user.email', read_only=True)
    submitted_at = serializers.DateTimeField(source='user.date_joined', read_only=True)

    class Meta:
        model = ShelterProfile
        fields = (
            'id', 'shelter_name', 'legal_name', 'organization_type', 'tax_code_vat',
            'official_email', 'address', 'city', 'province', 'postal_code',
            'phone_number', 'registrant_email', 'description', 'verification_status',
            'rejection_reason', 'submitted_at'
        )
        read_only_fields = fields


class ShelterRejectionSerializer(serializers.Serializer):
    reason = serializers.CharField(max_length=2000, allow_blank=False, trim_whitespace=True)


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
