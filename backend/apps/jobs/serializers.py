from rest_framework import serializers

from .models import JobOffer


class JobOfferSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source="id_jobOffer", read_only=True)
    admin_id = serializers.IntegerField(source="admin.id", read_only=True)
    cluster_id = serializers.IntegerField(source="cluster.id", read_only=True)
    cluster_number = serializers.IntegerField(source="cluster.k_value", read_only=True)
    company = serializers.CharField(source="entreprise", read_only=True)
    sector = serializers.CharField(source="secteur", read_only=True)
    location = serializers.CharField(source="localisation", read_only=True)
    contract_type = serializers.CharField(source="type_contrat", read_only=True)

    class Meta:
        model = JobOffer
        fields = [
            "id",
            "admin_id",
            "cluster_id",
            "cluster_number",
            "title",
            "description",
            "company",
            "sector",
            "location",
            "contract_type",
            "experience_required",
            "status",
            "published_at",
            "expires_at",
            "created_at",
        ]


class JobOfferCreateSerializer(serializers.ModelSerializer):
    company = serializers.CharField(source="entreprise")
    sector = serializers.CharField(source="secteur", required=False, allow_blank=True)
    location = serializers.CharField(source="localisation", required=False, allow_blank=True)
    contract_type = serializers.CharField(source="type_contrat", required=False, allow_blank=True)

    class Meta:
        model = JobOffer
        fields = [
            "admin",
            "cluster",
            "title",
            "description",
            "company",
            "sector",
            "location",
            "contract_type",
            "experience_required",
            "status",
            "published_at",
            "expires_at",
        ]
