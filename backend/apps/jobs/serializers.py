from rest_framework import serializers

from apps.users.models import Skill

from .models import JobOffer, JobSkill, SavedJob


class JobOfferSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source="id_jobOffer", read_only=True)
    admin_id = serializers.IntegerField(source="admin.id", read_only=True)
    cluster_id = serializers.IntegerField(source="cluster.id", read_only=True)
    cluster_number = serializers.IntegerField(source="cluster.k_value", read_only=True)
    company = serializers.CharField(source="entreprise", read_only=True)
    sector = serializers.CharField(source="secteur", read_only=True)
    location = serializers.CharField(source="localisation", read_only=True)
    contract_type = serializers.CharField(source="type_contrat", read_only=True)
    skills = serializers.SerializerMethodField()

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
            "salary",
            "skills",
            "status",
            "published_at",
            "expires_at",
            "created_at",
        ]

    def get_skills(self, obj):
        return [
            job_skill.skill.name
            for job_skill in obj.job_skills.select_related("skill").all()
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
            "salary",
            "status",
            "published_at",
            "expires_at",
        ]


class SavedJobSerializer(serializers.ModelSerializer):
    job_id = serializers.IntegerField(source="job.id_jobOffer")
    title = serializers.CharField(source="job.title")
    company = serializers.CharField(source="job.entreprise")
    location = serializers.CharField(source="job.localisation")

    class Meta:
        model = SavedJob
        fields = [
            "id",
            "job_id",
            "title",
            "company",
            "location",
            "saved_at",
        ]


class RecruiterJobSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source="id_jobOffer", read_only=True)
    company = serializers.CharField(source="entreprise")
    sector = serializers.CharField(source="secteur", required=False, allow_blank=True)
    location = serializers.CharField(source="localisation", required=False, allow_blank=True)
    contract_type = serializers.CharField(source="type_contrat", required=False, allow_blank=True)
    skills = serializers.ListField(
        child=serializers.CharField(max_length=150),
        required=False,
        allow_empty=True,
        write_only=True,
    )
    required_skills = serializers.SerializerMethodField(read_only=True)
    applications_count = serializers.SerializerMethodField()

    class Meta:
        model = JobOffer
        fields = [
            "id",
            "title",
            "description",
            "company",
            "sector",
            "location",
            "contract_type",
            "experience_required",
            "salary",
            "status",
            "expires_at",
            "published_at",
            "created_at",
            "skills",
            "required_skills",
            "applications_count",
        ]
        read_only_fields = ["published_at", "created_at"]

    def get_required_skills(self, obj):
        return [
            job_skill.skill.name
            for job_skill in obj.job_skills.select_related("skill").all()
        ]

    def get_applications_count(self, obj):
        annotated_count = getattr(obj, "applications_count", None)
        if annotated_count is not None:
            return annotated_count
        return obj.applications.count()

    def _sync_skills(self, job, skill_names):
        if skill_names is None:
            return

        cleaned_names = []
        for name in skill_names:
            cleaned = " ".join(str(name).strip().split())
            if cleaned:
                cleaned_names.append(cleaned)

        wanted = {name.lower() for name in cleaned_names}
        for job_skill in job.job_skills.select_related("skill"):
            if job_skill.skill.name.lower() not in wanted:
                job_skill.delete()

        for name in cleaned_names:
            skill = Skill.objects.filter(name__iexact=name).first()
            if skill is None:
                skill = Skill.objects.create(name=name, type=Skill.SkillType.HARD)
            JobSkill.objects.get_or_create(
                job=job,
                skill=skill,
                defaults={"is_required": True},
            )

    def create(self, validated_data):
        skill_names = validated_data.pop("skills", None)
        job = JobOffer.objects.create(**validated_data)
        self._sync_skills(job, skill_names)
        return job

    def update(self, instance, validated_data):
        skill_names = validated_data.pop("skills", None)
        for field, value in validated_data.items():
            setattr(instance, field, value)
        instance.save()
        self._sync_skills(instance, skill_names)
        return instance
