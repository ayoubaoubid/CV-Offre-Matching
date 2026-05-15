from rest_framework import serializers
from django.core.validators import URLValidator
from django.core.exceptions import ValidationError as DjangoValidationError

from .models import CompanyProfile, User


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()

    def validate_email(self, value):
        return value.strip().lower()


class RegisterSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(min_length=6)
    confirm_password = serializers.CharField(min_length=6)
    first_name = serializers.CharField(max_length=100)
    last_name = serializers.CharField(max_length=100)
    title = serializers.CharField(max_length=150, required=False, allow_blank=True)
    bio = serializers.CharField(required=False, allow_blank=True)
    location = serializers.CharField(max_length=150, required=False, allow_blank=True)
    experience_years = serializers.IntegerField(required=False, min_value=0, default=0)
    education_level = serializers.CharField(max_length=100, required=False, allow_blank=True)
    phone = serializers.CharField(max_length=20, required=False, allow_blank=True)
    linkedin_url = serializers.CharField(required=False, allow_blank=True)

    def validate_email(self, value):
        normalized_email = value.strip().lower()
        if User.objects.filter(email__iexact=normalized_email).exists():
            raise serializers.ValidationError("Cet email existe deja.")
        return normalized_email

    def validate(self, attrs):
        if attrs["password"] != attrs["confirm_password"]:
            raise serializers.ValidationError(
                {"confirm_password": "Les mots de passe ne correspondent pas."}
            )
        return attrs

    def validate_linkedin_url(self, value):
        cleaned_value = value.strip()
        if not cleaned_value:
            return ""
        if "://" not in cleaned_value:
            cleaned_value = f"https://{cleaned_value}"
        try:
            URLValidator()(cleaned_value)
        except DjangoValidationError:
            raise serializers.ValidationError("Lien LinkedIn invalide.")
        return cleaned_value


class RecruiterRegisterSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(min_length=6)
    confirm_password = serializers.CharField(min_length=6)
    first_name = serializers.CharField(max_length=100)
    last_name = serializers.CharField(max_length=100)
    company_name = serializers.CharField(max_length=180)
    sector = serializers.CharField(max_length=150, required=False, allow_blank=True)
    description = serializers.CharField(required=False, allow_blank=True)
    website = serializers.CharField(required=False, allow_blank=True)
    location = serializers.CharField(max_length=150, required=False, allow_blank=True)
    logo_url = serializers.CharField(required=False, allow_blank=True)
    professional_email = serializers.EmailField(required=False, allow_blank=True)
    phone = serializers.CharField(max_length=30, required=False, allow_blank=True)

    def validate_email(self, value):
        normalized_email = value.strip().lower()
        if User.objects.filter(email__iexact=normalized_email).exists():
            raise serializers.ValidationError("Cet email existe deja.")
        return normalized_email

    def validate(self, attrs):
        if attrs["password"] != attrs["confirm_password"]:
            raise serializers.ValidationError(
                {"confirm_password": "Les mots de passe ne correspondent pas."}
            )
        return attrs

    def validate_website(self, value):
        return self._validate_optional_url(value, "Site web invalide.")

    def validate_logo_url(self, value):
        return self._validate_optional_url(value, "URL du logo invalide.")

    def _validate_optional_url(self, value, message):
        cleaned_value = value.strip()
        if not cleaned_value:
            return ""
        if "://" not in cleaned_value:
            cleaned_value = f"https://{cleaned_value}"
        try:
            URLValidator()(cleaned_value)
        except DjangoValidationError:
            raise serializers.ValidationError(message)
        return cleaned_value


class ProfileUpdateSerializer(serializers.Serializer):
    first_name = serializers.CharField(max_length=100, required=False)
    last_name = serializers.CharField(max_length=100, required=False)
    title = serializers.CharField(max_length=150, required=False, allow_blank=True)
    bio = serializers.CharField(required=False, allow_blank=True)
    location = serializers.CharField(max_length=150, required=False, allow_blank=True)
    experience_years = serializers.IntegerField(required=False, min_value=0)
    education_level = serializers.CharField(max_length=100, required=False, allow_blank=True)
    phone = serializers.CharField(max_length=20, required=False, allow_blank=True)
    linkedin_url = serializers.CharField(required=False, allow_blank=True)
    skills = serializers.JSONField(required=False)
    cv_text = serializers.CharField(required=False, allow_blank=True)

    def validate_linkedin_url(self, value):
        cleaned_value = value.strip()
        if not cleaned_value:
            return ""
        if "://" not in cleaned_value:
            cleaned_value = f"https://{cleaned_value}"
        try:
            URLValidator()(cleaned_value)
        except DjangoValidationError:
            raise serializers.ValidationError("Lien LinkedIn invalide.")
        return cleaned_value


class CompanyProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = CompanyProfile
        fields = [
            "company_name",
            "sector",
            "description",
            "website",
            "location",
            "logo_url",
            "professional_email",
            "phone",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]
