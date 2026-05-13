import re
from functools import lru_cache
from pathlib import Path

import joblib
import spacy
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from sklearn.metrics.pairwise import cosine_similarity

from apps.jobs.models import JobOffer
from apps.users.models import CV
from apps.users.views import get_current_user


TOKEN_PATTERN = re.compile(r"\w+", re.UNICODE)
BAD_WORDS = {"acros", "casanca", "action", "activite"}
BASE_DIR = Path(__file__).resolve().parents[3]
VECTORIZER_PATH = BASE_DIR / "data_engine" / "models" / "tfidf_vectorizer.pkl"


def tokenize(text):
    return set(TOKEN_PATTERN.findall((text or "").lower()))


def jaccard_score(left_tokens, right_tokens):
    if not left_tokens and not right_tokens:
        return 0
    return len(left_tokens & right_tokens) / len(left_tokens | right_tokens)


@lru_cache(maxsize=1)
def get_vectorizer():
    return joblib.load(VECTORIZER_PATH)


@lru_cache(maxsize=1)
def get_nlp():
    return spacy.load("fr_core_news_sm")


def clean_raw_text(text):
    text = str(text or "").lower()
    text = re.sub(r"\d+", " ", text)
    text = re.sub(r"[^a-zA-ZÀ-ÿ\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def is_valid_token(token):
    lemma = token.lemma_.lower()
    return (
        token.is_alpha
        and not token.is_stop
        and len(lemma) > 3
        and len(lemma) <= 20
        and lemma.isalpha()
        and lemma not in BAD_WORDS
    )


def preprocess_for_matching(text):
    cleaned = clean_raw_text(text)
    if not cleaned:
        return ""

    doc = get_nlp()(cleaned)
    tokens = [token.lemma_.lower() for token in doc if is_valid_token(token)]
    return " ".join(tokens)


def build_cv_text(user, cv, user_skills):
    profile = getattr(user, "profile", None)
    parts = [
        cv.raw_text,
        " ".join(sorted(user_skills)),
    ]

    if profile:
        parts.extend([profile.title, profile.bio, profile.education_level])

    return " ".join(part for part in parts if part)


def build_job_text(job, job_skills):
    parts = [
        job.title,
        job.description,
        job.secteur,
        " ".join(sorted(job_skills)),
    ]
    return " ".join(part for part in parts if part)


def cosine_score(cv_text, job_text):
    processed_cv = preprocess_for_matching(cv_text)
    processed_job = preprocess_for_matching(job_text)
    if not processed_cv or not processed_job:
        return 0

    vectorizer = get_vectorizer()
    matrix = vectorizer.transform([processed_cv, processed_job])
    return float(cosine_similarity(matrix[0:1], matrix[1:2])[0][0])


def calculate_matching_score(user, cv, job, user_skills):
    profile = getattr(user, "profile", None)
    job_skills = {
        job_skill.skill.name.lower()
        for job_skill in job.job_skills.all()
    }

    cv_text = build_cv_text(user, cv, user_skills)
    job_text = build_job_text(job, job_skills)

    cv_tokens = tokenize(cv_text) | user_skills
    job_tokens = tokenize(job_text) | job_skills

    cosine = cosine_score(cv_text, job_text)
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

        if not VECTORIZER_PATH.exists():
            return Response(
                {"message": "Le modele TF-IDF du data_engine est introuvable."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        try:
            get_vectorizer()
            get_nlp()
        except Exception as exc:
            return Response(
                {"message": f"Le pipeline NLP du data_engine est indisponible: {exc}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
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

        results = sorted(results, key=lambda item: item["matching_score"], reverse=True)
        return Response(results)
