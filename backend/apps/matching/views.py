import re

from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from apps.jobs.models import JobOffer
from apps.users.models import CV
from apps.users.views import get_current_user


TOKEN_PATTERN = re.compile(r"\w+", re.UNICODE)


def tokenize(text):
    return set(TOKEN_PATTERN.findall((text or "").lower()))


def jaccard_score(left_tokens, right_tokens):
    if not left_tokens and not right_tokens:
        return 0
    return len(left_tokens & right_tokens) / len(left_tokens | right_tokens)


def cosine_score(cv_text, job_text):
    if not tokenize(cv_text) or not tokenize(job_text):
        return 0

    matrix = TfidfVectorizer(token_pattern=r"(?u)\b\w+\b").fit_transform([cv_text, job_text])
    return float(cosine_similarity(matrix[0:1], matrix[1:2])[0][0])


def calculate_matching_score(user, cv, job, user_skills):
    profile = getattr(user, "profile", None)
    job_skills = {
        job_skill.skill.name.lower()
        for job_skill in job.job_skills.all()
    }

    cv_tokens = tokenize(cv.raw_text) | user_skills
    job_tokens = tokenize(job.description) | tokenize(job.title) | job_skills

    cosine = cosine_score(cv.raw_text, job.description)
    jaccard = jaccard_score(cv_tokens, job_tokens)

    user_experience = getattr(profile, "experience_years", 0) if profile else 0
    exp_match = 1 if user_experience >= job.experience_required else 0

    user_location = (getattr(profile, "location", "") if profile else "").strip().lower()
    job_location = (job.localisation or "").strip().lower()
    geo_match = 1 if user_location and user_location in job_location else 0

    global_score = (
        0.50 * cosine
        + 0.25 * jaccard
        + 0.15 * exp_match
        + 0.10 * geo_match
    )

    return {
        "global_score": global_score,
        "cosine": cosine,
        "jaccard": jaccard,
        "exp_match": exp_match,
        "geo_match": geo_match,
    }


class MatchRecommendationsView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        user = get_current_user(request)
        if user is None:
            return Response(
                {"message": "Utilisateur non authentifie."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        cv = CV.objects.filter(user=user, is_active=True).order_by("-uploaded_at").first()
        if not cv:
            return Response(
                {"message": "Aucun CV actif trouve pour cet utilisateur."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        jobs = (
            JobOffer.objects.filter(status=JobOffer.Status.OPEN)
            .prefetch_related("job_skills__skill")
            .select_related("cluster")
        )

        user_skills = {
            user_skill.skill.name.lower()
            for user_skill in user.user_skills.select_related("skill")
        }

        results = []
        for job in jobs:
            score_data = calculate_matching_score(user, cv, job, user_skills)
            matching_percent = round(score_data["global_score"] * 100, 2)

            results.append(
                {
                    "id": job.pk,
                    "job_id": job.pk,
                    "title": job.title,
                    "company": job.entreprise,
                    "location": job.localisation,
                    "contract_type": job.type_contrat,
                    "score": matching_percent,
                    "matching_score": matching_percent,
                    "cosine_score": round(score_data["cosine"] * 100, 2),
                    "jaccard_score": round(score_data["jaccard"] * 100, 2),
                    "experience_match": score_data["exp_match"],
                    "location_match": score_data["geo_match"],
                }
            )

        results = sorted(
            results,
            key=lambda x: x["matching_score"],
            reverse=True,
        )

        return Response(results)
