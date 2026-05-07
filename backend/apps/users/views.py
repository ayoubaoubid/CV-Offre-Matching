from django.db import transaction
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.tokens import RefreshToken

from .models import CV, Profile, Skill, User, UserSkill
from .serializers import LoginSerializer, ProfileUpdateSerializer, RegisterSerializer


def parse_skills_payload(raw_skills):
    if raw_skills in (None, ""):
        return []

    if isinstance(raw_skills, str):
        chunks = raw_skills.replace("\n", ",").split(",")
        return [{"name": chunk.strip(), "level": ""} for chunk in chunks if chunk.strip()]

    parsed = []
    if isinstance(raw_skills, list):
        for item in raw_skills:
            if isinstance(item, str) and item.strip():
                parsed.append({"name": item.strip(), "level": ""})
            elif isinstance(item, dict):
                name = str(item.get("name", "")).strip()
                if name:
                    parsed.append(
                        {
                            "name": name,
                            "level": str(item.get("level", "")).strip(),
                        }
                    )
    return parsed


def sync_user_skills(user, raw_skills):
    parsed_skills = parse_skills_payload(raw_skills)
    wanted_names = {item["name"].lower() for item in parsed_skills}

    for user_skill in UserSkill.objects.filter(user=user).select_related("skill"):
        if user_skill.skill.name.lower() not in wanted_names:
            user_skill.delete()

    for item in parsed_skills:
        skill = Skill.objects.filter(name__iexact=item["name"]).first()
        if skill is None:
            skill = Skill.objects.create(
                name=item["name"],
                type=Skill.SkillType.HARD,
            )
        user_skill, _ = UserSkill.objects.get_or_create(user=user, skill=skill)
        user_skill.level = item["level"]
        user_skill.save(update_fields=["level"])


def save_cv_text(user, cv_text):
    if cv_text is None:
        return

    cv_text = str(cv_text).strip()
    active_cv = user.cvs.filter(is_active=True).order_by("-uploaded_at").first()

    if not cv_text:
        if active_cv and active_cv.raw_text:
            active_cv.raw_text = ""
            active_cv.save(update_fields=["raw_text"])
        return

    if active_cv is None:
        CV.objects.create(
            user=user,
            file_path=f"profiles/manual_cv_user_{user.id}.docx",
            file_type=CV.FileType.DOCX,
            raw_text=cv_text,
            is_active=True,
        )
        return

    active_cv.raw_text = cv_text
    active_cv.file_path = active_cv.file_path or f"profiles/manual_cv_user_{user.id}.docx"
    active_cv.file_type = active_cv.file_type or CV.FileType.DOCX
    active_cv.save(update_fields=["raw_text", "file_path", "file_type"])


def build_auth_payload(user):
    refresh = RefreshToken.for_user(user)
    return {
        "access": str(refresh.access_token),
        "refresh": str(refresh),
    }


def serialize_user(user):
    profile = getattr(user, "profile", None)
    active_cv = user.cvs.filter(is_active=True).order_by("-uploaded_at").first()
    skills = [
        {
            "id": user_skill.skill.id,
            "name": user_skill.skill.name,
            "level": user_skill.level,
        }
        for user_skill in user.user_skills.select_related("skill").order_by("skill__name")
    ]

    return {
        "id": user.id,
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "role": user.role,
        "profile": {
            "title": profile.title if profile else "",
            "bio": profile.bio if profile else "",
            "location": profile.location if profile else "",
            "experience_years": profile.experience_years if profile else 0,
            "education_level": profile.education_level if profile else "",
            "phone": profile.phone if profile else "",
            "linkedin_url": profile.linkedin_url if profile else "",
            "avatar_url": profile.avatar_url if profile else "",
        },
        "skills": skills,
        "cv": (
            {
                "id": active_cv.id,
                "file_path": active_cv.file_path,
                "file_type": active_cv.file_type,
                "raw_text": active_cv.raw_text,
                "uploaded_at": active_cv.uploaded_at,
            }
            if active_cv
            else None
        ),
        "has_completed_cv": bool(active_cv and active_cv.raw_text.strip()),
    }


def get_current_user(request):
    if getattr(request, "user", None) and request.user.is_authenticated:
        return request.user

    jwt_authentication = JWTAuthentication()
    try:
        auth_result = jwt_authentication.authenticate(request)
    except Exception:
        auth_result = None

    if auth_result:
        user, _token = auth_result
        return user

    user_id = request.headers.get("X-User-Id") or request.query_params.get("user_id")
    if not user_id and isinstance(request.data, dict):
        user_id = request.data.get("user_id")

    if not user_id:
        return None

    try:
        return User.objects.get(id=int(user_id))
    except (User.DoesNotExist, ValueError, TypeError):
        return None


class RegisterView(APIView):
    @transaction.atomic
    def post(self, request, *args, **kwargs):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        user = User.objects.create_user(
            email=data["email"],
            password=data["password"],
            first_name=data["first_name"],
            last_name=data["last_name"],
            role=User.Role.CANDIDATE,
        )

        Profile.objects.create(
            user=user,
            title=data.get("title", ""),
            bio=data.get("bio", ""),
            location=data.get("location", ""),
            experience_years=data.get("experience_years", 0),
            education_level=data.get("education_level", ""),
            phone=data.get("phone", ""),
            linkedin_url=data.get("linkedin_url", ""),
        )

        return Response(
            {
                "message": "Compte cree avec succes.",
                "user": serialize_user(user),
                "tokens": build_auth_payload(user),
            },
            status=status.HTTP_201_CREATED,
        )


class LoginView(APIView):
    def post(self, request, *args, **kwargs):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            user = User.objects.select_related("profile").get(
                email__iexact=data["email"].strip(),
            )
        except User.DoesNotExist:
            return Response(
                {"message": "Email ou mot de passe invalide."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        if not user.check_password(data["password"]):
            return Response(
                {"message": "Email ou mot de passe invalide."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        if not user.is_active:
            return Response(
                {"message": "Ce compte est desactive."},
                status=status.HTTP_403_FORBIDDEN,
            )

        Profile.objects.get_or_create(user=user)

        return Response(
            {
                "message": "Connexion reussie.",
                "user": serialize_user(user),
                "tokens": build_auth_payload(user),
            },
            status=status.HTTP_200_OK,
        )


class MeView(APIView):
    def get(self, request, *args, **kwargs):
        user = get_current_user(request)
        if user is None:
            return Response(
                {"message": "Utilisateur non authentifie."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        Profile.objects.get_or_create(user=user)
        return Response({"user": serialize_user(user)}, status=status.HTTP_200_OK)

    @transaction.atomic
    def put(self, request, *args, **kwargs):
        user = get_current_user(request)
        if user is None:
            return Response(
                {"message": "Utilisateur non authentifie."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        serializer = ProfileUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        if "first_name" in data:
            user.first_name = data["first_name"]
        if "last_name" in data:
            user.last_name = data["last_name"]
        user.save(update_fields=["first_name", "last_name", "updated_at"])

        profile, _ = Profile.objects.get_or_create(user=user)

        profile_fields = [
            "title",
            "bio",
            "location",
            "experience_years",
            "education_level",
            "phone",
            "linkedin_url",
        ]
        updated_fields = []
        for field in profile_fields:
            if field in data:
                setattr(profile, field, data[field])
                updated_fields.append(field)
        if updated_fields:
            profile.save(update_fields=updated_fields)

        if "skills" in data:
            sync_user_skills(user, data.get("skills"))

        if "cv_text" in data:
            save_cv_text(user, data.get("cv_text"))

        return Response(
            {
                "message": "Profil mis a jour avec succes.",
                "user": serialize_user(user),
            },
            status=status.HTTP_200_OK,
        )
