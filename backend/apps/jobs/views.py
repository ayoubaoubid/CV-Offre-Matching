from collections import Counter

from django.db.models import Count, Q
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.matching.models import Application, Notification
from apps.matching.views import calculate_matching_score
from apps.users.models import CV, User
from apps.users.views import get_current_user

from .models import JobOffer, SavedJob
from .serializers import (
    JobOfferCreateSerializer,
    JobOfferSerializer,
    RecruiterJobSerializer,
    SavedJobSerializer,
)


def require_recruiter(request):
    user = get_current_user(request)
    if user is None:
        return None, Response(
            {"message": "Utilisateur non authentifie."},
            status=status.HTTP_401_UNAUTHORIZED,
        )
    if user.role != User.Role.ADMIN:
        return None, Response(
            {"message": "Acces reserve aux recruteurs."},
            status=status.HTTP_403_FORBIDDEN,
        )
    return user, None


def serialize_candidate_match(candidate, cv, score_data):
    profile = getattr(candidate, "profile", None)
    skills = [
        user_skill.skill.name
        for user_skill in candidate.user_skills.select_related("skill").all()
    ]
    matching_percent = round(score_data["global_score"] * 100, 2)
    reasons = []
    if score_data["jaccard"] > 0:
        reasons.append("Competences proches")
    if score_data["exp_match"]:
        reasons.append("Experience suffisante")
    if score_data["geo_match"]:
        reasons.append("Localisation compatible")
    if score_data["cosine"] > 0.15:
        reasons.append("CV proche de l'offre")

    return {
        "id": candidate.id,
        "candidate_id": candidate.id,
        "name": candidate.get_full_name(),
        "email": candidate.email,
        "title": profile.title if profile else "",
        "location": profile.location if profile else "",
        "experience_years": profile.experience_years if profile else 0,
        "skills": skills,
        "score": matching_percent,
        "matching_score": matching_percent,
        "cosine_score": round(score_data["cosine"] * 100, 2),
        "jaccard_score": round(score_data["jaccard"] * 100, 2),
        "experience_match": score_data["exp_match"],
        "location_match": score_data["geo_match"],
        "reason": ", ".join(reasons) or "Profil partiellement compatible",
        "cv_text": cv.raw_text if cv else "",
    }


class JobOfferListCreateView(generics.ListCreateAPIView):
    queryset = JobOffer.objects.select_related("admin", "cluster").prefetch_related(
        "job_skills__skill"
    )

    def get_serializer_class(self):
        if self.request.method == "POST":
            return JobOfferCreateSerializer
        return JobOfferSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        job = serializer.save()
        output_serializer = JobOfferSerializer(job)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)


class SaveJobView(APIView):
    def post(self, request, job_id):
        user = get_current_user(request)
        if user is None:
            return Response(
                {"message": "Utilisateur non authentifie."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        job = JobOffer.objects.get(pk=job_id)
        _saved, created = SavedJob.objects.get_or_create(user=user, job=job)
        return Response({"saved": True, "created": created})

    def delete(self, request, job_id):
        user = get_current_user(request)
        if user is None:
            return Response(
                {"message": "Utilisateur non authentifie."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        job = JobOffer.objects.get(pk=job_id)
        SavedJob.objects.filter(user=user, job=job).delete()
        return Response({"saved": False}, status=status.HTTP_204_NO_CONTENT)


class UserSavedJobsView(APIView):
    def get(self, request):
        user = get_current_user(request)
        if user is None:
            return Response(
                {"message": "Utilisateur non authentifie."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        jobs = SavedJob.objects.filter(user=user)
        serializer = SavedJobSerializer(jobs, many=True)
        return Response(serializer.data)


class JobsMapStatsView(APIView):
    def get(self, request):
        jobs = JobOffer.objects.all()
        city_counter = Counter()

        for job in jobs:
            city = job.localisation.strip().lower()
            if city:
                city_counter[city] += 1

        total = sum(city_counter.values()) or 1
        results = [
            {
                "city": city,
                "count": count,
                "percent": round((count / total) * 100, 2),
            }
            for city, count in city_counter.items()
        ]
        return Response(results)


class RecruiterDashboardView(APIView):
    def get(self, request):
        user, error_response = require_recruiter(request)
        if error_response:
            return error_response

        jobs = JobOffer.objects.filter(admin=user)
        applications = Application.objects.filter(job__admin=user).select_related(
            "user",
            "job",
        )
        scores = [
            application.matching_score
            for application in applications
            if application.matching_score is not None
        ]
        latest_applications = applications.order_by("-applied_at")[:5]

        return Response(
            {
                "total_offers": jobs.count(),
                "active_offers": jobs.filter(status=JobOffer.Status.OPEN).count(),
                "draft_offers": jobs.filter(status=JobOffer.Status.DRAFT).count(),
                "closed_offers": jobs.filter(status=JobOffer.Status.CLOSED).count(),
                "total_applications": applications.count(),
                "recommended_candidates": CV.objects.filter(
                    user__role=User.Role.CANDIDATE,
                    is_active=True,
                    raw_text__gt="",
                ).count(),
                "average_matching_score": round(sum(scores) / len(scores) * 100, 2)
                if scores
                else 0,
                "latest_applications": [
                    {
                        "id": application.id,
                        "candidate_name": application.user.get_full_name(),
                        "job_title": application.job.title,
                        "status": application.status,
                        "score": round((application.matching_score or 0) * 100, 2),
                        "applied_at": application.applied_at,
                    }
                    for application in latest_applications
                ],
            }
        )


class RecruiterJobListCreateView(APIView):
    def get(self, request):
        user, error_response = require_recruiter(request)
        if error_response:
            return error_response

        status_filter = request.query_params.get("status", "")
        jobs = (
            JobOffer.objects.filter(admin=user)
            .annotate(applications_count=Count("applications"))
            .prefetch_related("job_skills__skill")
            .order_by("-created_at")
        )
        if status_filter:
            jobs = jobs.filter(status=status_filter)

        return Response(RecruiterJobSerializer(jobs, many=True).data)

    def post(self, request):
        user, error_response = require_recruiter(request)
        if error_response:
            return error_response

        serializer = RecruiterJobSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        job = serializer.save(admin=user)
        return Response(
            RecruiterJobSerializer(job).data,
            status=status.HTTP_201_CREATED,
        )


class RecruiterJobDetailView(APIView):
    def get_job(self, user, job_id):
        return (
            JobOffer.objects.filter(admin=user, pk=job_id)
            .annotate(applications_count=Count("applications"))
            .prefetch_related("job_skills__skill")
            .first()
        )

    def get(self, request, job_id):
        user, error_response = require_recruiter(request)
        if error_response:
            return error_response

        job = self.get_job(user, job_id)
        if job is None:
            return Response({"message": "Offre introuvable."}, status=status.HTTP_404_NOT_FOUND)
        return Response(RecruiterJobSerializer(job).data)

    def put(self, request, job_id):
        user, error_response = require_recruiter(request)
        if error_response:
            return error_response

        job = self.get_job(user, job_id)
        if job is None:
            return Response({"message": "Offre introuvable."}, status=status.HTTP_404_NOT_FOUND)
        serializer = RecruiterJobSerializer(job, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        job = serializer.save()
        return Response(RecruiterJobSerializer(job).data)

    def delete(self, request, job_id):
        user, error_response = require_recruiter(request)
        if error_response:
            return error_response

        job = self.get_job(user, job_id)
        if job is None:
            return Response({"message": "Offre introuvable."}, status=status.HTTP_404_NOT_FOUND)
        job.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class RecruiterJobStatusView(APIView):
    def patch(self, request, job_id):
        user, error_response = require_recruiter(request)
        if error_response:
            return error_response

        job = JobOffer.objects.filter(admin=user, pk=job_id).first()
        if job is None:
            return Response({"message": "Offre introuvable."}, status=status.HTTP_404_NOT_FOUND)

        next_status = request.data.get("status")
        allowed_statuses = {choice[0] for choice in JobOffer.Status.choices}
        if next_status not in allowed_statuses:
            return Response(
                {"message": "Statut d'offre invalide."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        job.status = next_status
        job.save(update_fields=["status"])
        return Response(RecruiterJobSerializer(job).data)


class JobCandidatesView(APIView):
    def get(self, request, job_id):
        user, error_response = require_recruiter(request)
        if error_response:
            return error_response

        job = (
            JobOffer.objects.filter(admin=user, pk=job_id)
            .prefetch_related("job_skills__skill")
            .first()
        )
        if job is None:
            return Response({"message": "Offre introuvable."}, status=status.HTTP_404_NOT_FOUND)

        candidates = (
            User.objects.filter(role=User.Role.CANDIDATE, cvs__is_active=True)
            .exclude(cvs__raw_text="")
            .select_related("profile")
            .prefetch_related("user_skills__skill", "cvs")
            .distinct()
        )

        results = []
        for candidate in candidates:
            cv = candidate.cvs.filter(is_active=True).order_by("-uploaded_at").first()
            if not cv:
                continue
            user_skills = {
                user_skill.skill.name.lower()
                for user_skill in candidate.user_skills.select_related("skill")
            }
            score_data = calculate_matching_score(candidate, cv, job, user_skills)
            results.append(serialize_candidate_match(candidate, cv, score_data))

        results = sorted(results, key=lambda item: item["matching_score"], reverse=True)
        limit = int(request.query_params.get("limit", 30))
        return Response(results[:limit])


class InviteCandidateView(APIView):
    def post(self, request, job_id, candidate_id):
        user, error_response = require_recruiter(request)
        if error_response:
            return error_response

        job = JobOffer.objects.filter(admin=user, pk=job_id).first()
        if job is None:
            return Response({"message": "Offre introuvable."}, status=status.HTTP_404_NOT_FOUND)

        candidate = User.objects.filter(
            id=candidate_id,
            role=User.Role.CANDIDATE,
        ).first()
        if candidate is None:
            return Response({"message": "Candidat introuvable."}, status=status.HTTP_404_NOT_FOUND)

        recruiter_name = user.get_full_name() or user.email
        Notification.objects.create(
            user=candidate,
            job=job,
            type=Notification.Type.NEW_OFFER,
            title="Invitation a postuler",
            message=(
                f"{recruiter_name} vous invite a postuler pour l'offre "
                f"\"{job.title}\" chez {job.entreprise}."
            ),
        )

        return Response(
            {"message": "Invitation envoyee au candidat."},
            status=status.HTTP_201_CREATED,
        )
