import logging
import re
import unicodedata
from functools import lru_cache
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import spacy
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.neighbors import NearestNeighbors

from apps.jobs.models import JobOffer
from apps.users.models import CV, User
from apps.users.views import get_current_user

from .models import Application, Notification


# Section modifiee: logger pour les warnings de fallback clustering.
logger = logging.getLogger(__name__)


# Section modifiee: constantes mises a jour pour le nouveau vectorizer DBSCAN.
TOKEN_PATTERN = re.compile(r"\w+", re.UNICODE)
BAD_WORDS = {"acros", "casanca", "action", "activite"}
BASE_DIR = Path(__file__).resolve().parents[3]
MODEL_DIR = BASE_DIR / "data_engine" / "models"
CLUSTERING_DIR = BASE_DIR / "data_engine" / "clustering"
VECTORIZER_PATH = MODEL_DIR / "tfidf_vectorizer_dbscan_now.pkl"
DBSCAN_PATH = MODEL_DIR / "dbscan_model_now.pkl"
DBSCAN_DATASET_PATH = CLUSTERING_DIR / "dbscan_clustered_offres_now.csv"


def resolve_existing_path(primary_path, *fallback_paths):
    for candidate in (primary_path, *fallback_paths):
        if candidate.exists():
            return candidate
    return primary_path


VECTORIZER_PATH = resolve_existing_path(
    VECTORIZER_PATH,
    MODEL_DIR / "tfidf_vectorizer_dbscan.pkl",
)
DBSCAN_PATH = resolve_existing_path(
    DBSCAN_PATH,
    MODEL_DIR / "dbscan_model.pkl",
)
DBSCAN_DATASET_PATH = resolve_existing_path(
    DBSCAN_DATASET_PATH,
    CLUSTERING_DIR / "dbscan_clustered_offres_new.csv",
    CLUSTERING_DIR / "dbscan_clustered_offres.csv",
)
MAX_OUTLIER_RESULTS = 50


def tokenize(text):
    return set(TOKEN_PATTERN.findall((text or "").lower()))


def jaccard_score(left_tokens, right_tokens):
    if not left_tokens and not right_tokens:
        return 0
    return len(left_tokens & right_tokens) / len(left_tokens | right_tokens)


# chargement du nouveau vectorizer DBSCAN-compatible.
@lru_cache(maxsize=1)
def get_vectorizer():
    return joblib.load(VECTORIZER_PATH)


# chargement mis en cache du modele DBSCAN.
@lru_cache(maxsize=1)
def get_dbscan():
    return joblib.load(DBSCAN_PATH)


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


# vectorisation du CV avec pour reutiliser le modele entraine.
def vectorize_cv(cv_text_clean):
    if not cv_text_clean:
        return None
    vectorizer = get_vectorizer()
    return vectorizer.transform([cv_text_clean])


# normalisation pour apparier les offres Django avec le CSV DBSCAN.
def normalize_dbscan_value(value):
    if value is None:
        return ""
    text = str(value).strip()
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    return " ".join(text.lower().split())


@lru_cache(maxsize=1)
def load_dbscan_indexed_rows():
    if not DBSCAN_DATASET_PATH.exists():
        raise FileNotFoundError(f"Dataset DBSCAN introuvable: {DBSCAN_DATASET_PATH}")

    df = pd.read_csv(DBSCAN_DATASET_PATH).fillna("")
    cluster_column = "cluster_dbscan" if "cluster_dbscan" in df.columns else "cluster"
    indexed_rows = {}

    for _, row in df.iterrows():
        record = {
            "titre": normalize_dbscan_value(row.get("titre")),
            "entreprise": normalize_dbscan_value(row.get("entreprise")),
            "secteur": normalize_dbscan_value(row.get("secteur")),
            "localisation": normalize_dbscan_value(row.get("localisation")),
            "contrat": normalize_dbscan_value(row.get("contrat")),
            "cluster_label": int(row.get(cluster_column)),
        }
        key = (record["titre"], record["entreprise"])
        indexed_rows.setdefault(key, []).append(record)

    return indexed_rows


def dedupe_dbscan_candidates(candidates):
    unique = {}
    for row in candidates:
        key = (
            row["titre"],
            row["entreprise"],
            row["secteur"],
            row["localisation"],
            row["contrat"],
            row["cluster_label"],
        )
        unique.setdefault(key, row)
    return list(unique.values())


def get_job_dbscan_label(job, indexed_rows):
    candidates = dedupe_dbscan_candidates(
        indexed_rows.get(
            (
                normalize_dbscan_value(job.title),
                normalize_dbscan_value(job.entreprise),
            ),
            [],
        )
    )

    if not candidates:
        return None
    if len(candidates) == 1:
        return candidates[0]["cluster_label"]

    filters = [
        ("localisation", lambda row: row["localisation"] == normalize_dbscan_value(job.localisation)),
        ("secteur", lambda row: row["secteur"] == normalize_dbscan_value(job.secteur)),
        ("contrat", lambda row: row["contrat"] == normalize_dbscan_value(job.type_contrat)),
    ]

    for _, predicate in filters:
        narrowed = [row for row in candidates if predicate(row)]
        if narrowed:
            candidates = dedupe_dbscan_candidates(narrowed)
        if len(candidates) == 1:
            return candidates[0]["cluster_label"]

    cluster_labels = {row["cluster_label"] for row in candidates}
    if len(cluster_labels) == 1:
        return next(iter(cluster_labels))
    return None


# preparation des vecteurs offres pour le clustering DBSCAN.
def build_job_vectors_for_clustering(jobs_with_vectors, dbscan_labels):
    jobs_to_vectorize = []
    processed_texts = []
    vectors = []
    cluster_ids = []

    for job in jobs_with_vectors:
        cluster_label = dbscan_labels.get(job.pk)
        if cluster_label is None:
            continue

        if job.tfidf_vector:
            try:
                vector = np.asarray(job.tfidf_vector, dtype=float)
            except (TypeError, ValueError):
                vector = None
            if vector is not None and vector.ndim == 1 and vector.size > 0:
                vectors.append(vector)
                cluster_ids.append(cluster_label)
                continue

        job_skills = {
            job_skill.skill.name.lower()
            for job_skill in job.job_skills.all()
        }
        job_text_clean = preprocess_for_matching(build_job_text(job, job_skills))
        if not job_text_clean:
            continue

        jobs_to_vectorize.append(job)
        processed_texts.append(job_text_clean)

    if processed_texts:
        job_matrix = get_vectorizer().transform(processed_texts)
        for index, job in enumerate(jobs_to_vectorize):
            vectors.append(job_matrix[index].toarray()[0])
            cluster_ids.append(dbscan_labels[job.pk])

    return vectors, cluster_ids


# attribution d'un cluster au CV par plus proches voisins,
# car DBSCAN n'expose pas predict() pour de nouveaux points.
def find_cv_cluster(vec_cv, jobs_with_vectors, dbscan_labels):
    if vec_cv is None:
        return None

    vectors, cluster_ids = build_job_vectors_for_clustering(jobs_with_vectors, dbscan_labels)

    if len(vectors) < 5:
        return None

    try:
        matrix_offres = np.array(vectors, dtype=float)
        nbrs = NearestNeighbors(n_neighbors=7, metric="cosine")
        nbrs.fit(matrix_offres)
        cv_array = vec_cv.toarray() if hasattr(vec_cv, "toarray") else vec_cv
        _, indices = nbrs.kneighbors(cv_array)
    except Exception as exc:
        logger.warning("Impossible de determiner le cluster du CV: %s", exc)
        return None

    clusters_voisins = [
        cluster_ids[i]
        for i in indices[0]
        if cluster_ids[i] is not None
    ]
    if not clusters_voisins:
        return None

    return max(set(clusters_voisins), key=clusters_voisins.count)


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

        cv = CV.objects.filter(
            user=user, is_active=True
        ).order_by("-uploaded_at").first()
        if not cv:
            return Response(
                {"message": "Aucun CV actif trouve pour cet utilisateur."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Section modifiee: le vectorizer reste obligatoire, DBSCAN devient optionnel.
        if not VECTORIZER_PATH.exists():
            return Response(
                {"message": "Le modele TF-IDF du data_engine est introuvable."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        dbscan_available = DBSCAN_PATH.exists()
        if not dbscan_available:
            logger.warning(
                "Modele DBSCAN introuvable a %s. Fallback sur toutes les offres.",
                DBSCAN_PATH,
            )

        try:
            get_vectorizer()
            get_nlp()
            if dbscan_available:
                get_dbscan()
        except Exception as exc:
            if dbscan_available:
                try:
                    get_dbscan()
                except Exception as dbscan_exc:
                    logger.warning(
                        "DBSCAN indisponible, fallback sur toutes les offres: %s",
                        dbscan_exc,
                    )
                    dbscan_available = False
            if not dbscan_available:
                try:
                    get_vectorizer()
                    get_nlp()
                except Exception as base_exc:
                    return Response(
                        {"message": f"Le pipeline NLP est indisponible: {base_exc}"},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    )
            else:
                return Response(
                    {"message": f"Le pipeline NLP est indisponible: {exc}"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

        jobs_all = list(
            JobOffer.objects.filter(status=JobOffer.Status.OPEN)
            .prefetch_related("job_skills__skill")
            .select_related("cluster")
        )

        user_skills = {
            user_skill.skill.name.lower()
            for user_skill in user.user_skills.select_related("skill")
        }

        # Section modifiee: preparation et vectorisation du CV pour le clustering.
        cv_text_clean = preprocess_for_matching(
            build_cv_text(user, cv, user_skills)
        )
        vec_cv = vectorize_cv(cv_text_clean)

        dbscan_dataset_available = DBSCAN_DATASET_PATH.exists()
        dbscan_labels = {}
        if dbscan_available and dbscan_dataset_available:
            try:
                indexed_rows = load_dbscan_indexed_rows()
                dbscan_labels = {
                    job.pk: label
                    for job in jobs_all
                    for label in [get_job_dbscan_label(job, indexed_rows)]
                    if label is not None
                }
            except Exception as exc:
                logger.warning(
                    "Dataset DBSCAN indisponible, fallback sur toutes les offres: %s",
                    exc,
                )
                dbscan_labels = {}
        elif dbscan_available:
            logger.warning(
                "Dataset DBSCAN introuvable a %s. Fallback sur toutes les offres.",
                DBSCAN_DATASET_PATH,
            )

        jobs_with_vectors = [job for job in jobs_all if job.pk in dbscan_labels]

        # Section modifiee: si DBSCAN est dispo, on tente un rattachement au cluster.
        cluster_cv = None
        if dbscan_available and dbscan_labels:
            cluster_cv = find_cv_cluster(vec_cv, jobs_with_vectors, dbscan_labels)

        # Section modifiee: si le CV tombe dans le cluster -1, on affiche seulement les outliers.
        # Sinon, on affiche seulement les offres du meme cluster DBSCAN.
        if cluster_cv is not None:
            jobs_to_score = [
                job for job in jobs_all
                if dbscan_labels.get(job.pk) == cluster_cv
            ]
            cluster_used = cluster_cv
        else:
            jobs_to_score = jobs_all
            cluster_used = None

        results = []
        for job in jobs_to_score:
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
                    "description": job.description,
                    "score": matching_percent,
                    "matching_score": matching_percent,
                    "cosine_score": round(score_data["cosine"] * 100, 2),
                    "jaccard_score": round(score_data["jaccard"] * 100, 2),
                    "experience_match": score_data["exp_match"],
                    "location_match": score_data["geo_match"],
                    "cluster_id": cluster_used,
                }
            )

        results = sorted(
            results,
            key=lambda item: item["matching_score"],
            reverse=True,
        )
        if cluster_used == -1:
            results = results[:MAX_OUTLIER_RESULTS]
        return Response(results)


def serialize_application(application):
    profile = getattr(application.user, "profile", None)
    return {
        "id": application.id,
        "candidate_id": application.user.id,
        "candidate_name": application.user.get_full_name(),
        "candidate_email": application.user.email,
        "candidate_location": profile.location if profile else "",
        "candidate_title": profile.title if profile else "",
        "job_id": application.job.pk,
        "job_title": application.job.title,
        "job_company": application.job.entreprise,
        "status": application.status,
        "cover_letter": application.cover_letter,
        "internal_note": application.internal_note,
        "matching_score": round((application.matching_score or 0) * 100, 2),
        "cosine_score": round((application.cosine_score or 0) * 100, 2),
        "jaccard_score": round((application.jaccard_score or 0) * 100, 2),
        "experience_match": application.exp_match,
        "location_match": application.geo_match,
        "applied_at": application.applied_at,
        "reviewed_at": application.reviewed_at,
        "cv_text": application.cv.raw_text if application.cv else "",
    }


def serialize_notification(notification):
    application = notification.application
    return {
        "id": notification.id,
        "type": notification.type,
        "title": notification.title,
        "message": notification.message,
        "is_read": notification.is_read,
        "created_at": notification.created_at,
        "application_id": application.id if application else None,
        "job_id": application.job_id if application else None,
        "job_title": application.job.title if application else "",
    }


class CandidateNotificationsView(APIView):
    def get(self, request):
        user = get_current_user(request)
        if user is None:
            return Response(
                {"message": "Utilisateur non authentifie."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        notifications = Notification.objects.filter(user=user).select_related(
            "application",
            "application__job",
        )
        return Response([serialize_notification(item) for item in notifications])


class CandidateNotificationReadView(APIView):
    def patch(self, request, notification_id):
        user = get_current_user(request)
        if user is None:
            return Response(
                {"message": "Utilisateur non authentifie."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        notification = Notification.objects.filter(id=notification_id, user=user).first()
        if notification is None:
            return Response(
                {"message": "Notification introuvable."},
                status=status.HTTP_404_NOT_FOUND,
            )

        notification.mark_as_read()
        return Response(serialize_notification(notification))


class RecruiterApplicationsView(APIView):
    def get(self, request):
        user = get_current_user(request)
        if user is None:
            return Response(
                {"message": "Utilisateur non authentifie."},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        if user.role != User.Role.ADMIN:
            return Response(
                {"message": "Acces reserve aux recruteurs."},
                status=status.HTTP_403_FORBIDDEN,
            )

        applications = Application.objects.filter(job__admin=user).select_related(
            "user",
            "user__profile",
            "job",
            "cv",
        )
        job_id = request.query_params.get("job_id")
        status_filter = request.query_params.get("status")
        if job_id:
            applications = applications.filter(job_id=job_id)
        if status_filter:
            applications = applications.filter(status=status_filter)

        return Response([serialize_application(app) for app in applications])


class RecruiterApplicationStatusView(APIView):
    def patch(self, request, application_id):
        user = get_current_user(request)
        if user is None:
            return Response(
                {"message": "Utilisateur non authentifie."},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        if user.role != User.Role.ADMIN:
            return Response(
                {"message": "Acces reserve aux recruteurs."},
                status=status.HTTP_403_FORBIDDEN,
            )

        application = (
            Application.objects.filter(id=application_id, job__admin=user)
            .select_related("user", "user__profile", "job", "cv")
            .first()
        )
        if application is None:
            return Response(
                {"message": "Candidature introuvable."},
                status=status.HTTP_404_NOT_FOUND,
            )

        next_status = request.data.get("status")
        allowed_statuses = {choice[0] for choice in Application.Status.choices}
        if next_status not in allowed_statuses:
            return Response(
                {"message": "Statut de candidature invalide."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        application.status = next_status
        application.internal_note = request.data.get(
            "internal_note",
            application.internal_note,
        )
        application.reviewed_by = user
        application.reviewed_at = timezone.now()
        application.save(
            update_fields=[
                "status",
                "internal_note",
                "reviewed_by",
                "reviewed_at",
            ]
        )
        return Response(serialize_application(application))
