"""
Seed script for static application data.

Usage:
    python seed.py
"""

import os
import sys

import django


sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from apps.users.models import CV, Profile, Skill, User, UserSkill


GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
RESET = "\033[0m"
BOLD = "\033[1m"


def ok(message):
    print(f"  {GREEN}OK{RESET}  {message}")


def skip(message):
    print(f"  {YELLOW}SKIP{RESET}  {message}")


def err(message):
    print(f"  {RED}ERR{RESET}  {message}")


def title(message):
    print(f"\n{BOLD}{'-' * 50}\n  {message}\n{'-' * 50}{RESET}")


USER_FIXTURES = [
    {
        "email": "admin.demo@cvmatch.test",
        "legacy_emails": ["admin@cvmatch.com"],
        "password": "admin123",
        "first_name": "Admin",
        "last_name": "Demo",
        "role": User.Role.ADMIN,
    },
    {
        "email": "recruteur.demo@cvmatch.test",
        "legacy_emails": ["recruteur@cvmatch.com"],
        "password": "admin123",
        "first_name": "Recruteur",
        "last_name": "Demo",
        "role": User.Role.ADMIN,
    },
    {
        "email": "candidate01@cvmatch.test",
        "legacy_emails": ["ahmed.benali@cvmatch.com"],
        "password": "test1234",
        "first_name": "Candidat",
        "last_name": "Un",
        "role": User.Role.CANDIDATE,
    },
    {
        "email": "candidate02@cvmatch.test",
        "legacy_emails": ["sara.idrissi@cvmatch.com"],
        "password": "test1234",
        "first_name": "Candidat",
        "last_name": "Deux",
        "role": User.Role.CANDIDATE,
    },
    {
        "email": "candidate03@cvmatch.test",
        "legacy_emails": ["youssef.amrani@cvmatch.com"],
        "password": "test1234",
        "first_name": "Candidat",
        "last_name": "Trois",
        "role": User.Role.CANDIDATE,
    },
    {
        "email": "candidate04@cvmatch.test",
        "legacy_emails": ["hind.chakir@cvmatch.com"],
        "password": "test1234",
        "first_name": "Candidat",
        "last_name": "Quatre",
        "role": User.Role.CANDIDATE,
    },
]


PROFILE_FIXTURES = [
    {
        "email": "candidate01@cvmatch.test",
        "title": "Data Scientist",
        "bio": "Profil fictif de demonstration pour tester la data science et les projets NLP.",
        "location": "Ville Demo 1",
        "experience_years": 3,
        "education_level": "Master Data Science",
        "phone": "0600000001",
        "linkedin_url": "https://linkedin.example/demo-candidate-01",
    },
    {
        "email": "candidate02@cvmatch.test",
        "title": "Developpeuse Full Stack",
        "bio": "Profil fictif de demonstration pour tester React, Django et les formulaires.",
        "location": "Ville Demo 2",
        "experience_years": 2,
        "education_level": "Licence Informatique",
        "phone": "0600000002",
        "linkedin_url": "https://linkedin.example/demo-candidate-02",
    },
    {
        "email": "candidate03@cvmatch.test",
        "title": "Machine Learning Engineer",
        "bio": "Profil fictif de demonstration pour tester le deep learning et les workflows ML.",
        "location": "Ville Demo 3",
        "experience_years": 4,
        "education_level": "Master IA",
        "phone": "0600000003",
        "linkedin_url": "https://linkedin.example/demo-candidate-03",
    },
    {
        "email": "candidate04@cvmatch.test",
        "title": "Data Analyst",
        "bio": "Profil fictif de demonstration pour tester le reporting et la visualisation.",
        "location": "Ville Demo 4",
        "experience_years": 1,
        "education_level": "Licence IASD",
        "phone": "0600000004",
        "linkedin_url": "https://linkedin.example/demo-candidate-04",
    },
]


CV_FIXTURES = [
    {
        "email": "candidate01@cvmatch.test",
        "file_path": "cvs/demo_candidate_01_cv.pdf",
        "file_type": CV.FileType.PDF,
        "raw_text": "Candidat Un - Data Scientist - Python, Machine Learning, NLP, Pandas, Scikit-learn, SQL, Django, Git, Docker",
    },
    {
        "email": "candidate02@cvmatch.test",
        "file_path": "cvs/demo_candidate_02_cv.pdf",
        "file_type": CV.FileType.PDF,
        "raw_text": "Candidat Deux - Full Stack Developer - React, Django, JavaScript, HTML, CSS, REST API, Git, MySQL, PostgreSQL",
    },
    {
        "email": "candidate03@cvmatch.test",
        "file_path": "cvs/demo_candidate_03_cv.pdf",
        "file_type": CV.FileType.PDF,
        "raw_text": "Candidat Trois - ML Engineer - Python, TensorFlow, PyTorch, Deep Learning, NLP, Docker, Linux, Git",
    },
    {
        "email": "candidate04@cvmatch.test",
        "file_path": "cvs/demo_candidate_04_cv.pdf",
        "file_type": CV.FileType.PDF,
        "raw_text": "Candidat Quatre - Data Analyst - SQL, Power BI, Tableau, Python, Pandas, Excel, Matplotlib, Communication",
    },
]


USER_SKILL_FIXTURES = [
    {
        "email": "candidate01@cvmatch.test",
        "skills": [
            ("Python", "avance"),
            ("Machine Learning", "avance"),
            ("NLP", "intermediaire"),
            ("Pandas", "avance"),
            ("Scikit-learn", "intermediaire"),
            ("SQL", "intermediaire"),
            ("Django", "debutant"),
            ("Git", "intermediaire"),
            ("Communication", "avance"),
        ],
    },
    {
        "email": "candidate02@cvmatch.test",
        "skills": [
            ("React", "avance"),
            ("Django", "avance"),
            ("JavaScript", "avance"),
            ("HTML/CSS", "avance"),
            ("REST API", "intermediaire"),
            ("Git", "avance"),
            ("MySQL", "intermediaire"),
            ("PostgreSQL", "debutant"),
            ("Travail en equipe", "avance"),
        ],
    },
    {
        "email": "candidate03@cvmatch.test",
        "skills": [
            ("Python", "expert"),
            ("TensorFlow", "avance"),
            ("PyTorch", "avance"),
            ("Deep Learning", "avance"),
            ("NLP", "avance"),
            ("Scikit-learn", "avance"),
            ("Docker", "intermediaire"),
            ("Linux", "intermediaire"),
            ("Git", "avance"),
            ("Autonomie", "expert"),
        ],
    },
    {
        "email": "candidate04@cvmatch.test",
        "skills": [
            ("SQL", "avance"),
            ("Power BI", "avance"),
            ("Tableau", "intermediaire"),
            ("Python", "intermediaire"),
            ("Pandas", "intermediaire"),
            ("Matplotlib", "debutant"),
            ("Communication", "expert"),
            ("Gestion du temps", "avance"),
        ],
    },
]


def seed_skills():
    title("1. Creation des competences")

    skills_data = [
        {"name": "Python", "type": "hard", "category": "Programmation"},
        {"name": "R", "type": "hard", "category": "Programmation"},
        {"name": "Machine Learning", "type": "hard", "category": "Data Science"},
        {"name": "Deep Learning", "type": "hard", "category": "Data Science"},
        {"name": "NLP", "type": "hard", "category": "Data Science"},
        {"name": "TensorFlow", "type": "hard", "category": "Data Science"},
        {"name": "PyTorch", "type": "hard", "category": "Data Science"},
        {"name": "Scikit-learn", "type": "hard", "category": "Data Science"},
        {"name": "Pandas", "type": "hard", "category": "Data Science"},
        {"name": "NumPy", "type": "hard", "category": "Data Science"},
        {"name": "Matplotlib", "type": "hard", "category": "Data Science"},
        {"name": "Power BI", "type": "hard", "category": "Data Science"},
        {"name": "Tableau", "type": "hard", "category": "Data Science"},
        {"name": "Django", "type": "hard", "category": "Framework"},
        {"name": "FastAPI", "type": "hard", "category": "Framework"},
        {"name": "Flask", "type": "hard", "category": "Framework"},
        {"name": "React", "type": "hard", "category": "Frontend"},
        {"name": "JavaScript", "type": "hard", "category": "Programmation"},
        {"name": "HTML/CSS", "type": "hard", "category": "Frontend"},
        {"name": "REST API", "type": "hard", "category": "Architecture"},
        {"name": "SQL", "type": "hard", "category": "Base de donnees"},
        {"name": "MySQL", "type": "hard", "category": "Base de donnees"},
        {"name": "PostgreSQL", "type": "hard", "category": "Base de donnees"},
        {"name": "MongoDB", "type": "hard", "category": "Base de donnees"},
        {"name": "Git", "type": "hard", "category": "Outils"},
        {"name": "Docker", "type": "hard", "category": "DevOps"},
        {"name": "Linux", "type": "hard", "category": "Systeme"},
        {"name": "Web Scraping", "type": "hard", "category": "Data Science"},
        {"name": "Scrapy", "type": "hard", "category": "Data Science"},
        {"name": "Communication", "type": "soft", "category": "Interpersonnel"},
        {"name": "Travail en equipe", "type": "soft", "category": "Interpersonnel"},
        {"name": "Autonomie", "type": "soft", "category": "Personnel"},
        {"name": "Resolution de problemes", "type": "soft", "category": "Analytique"},
        {"name": "Gestion du temps", "type": "soft", "category": "Organisation"},
    ]

    created = 0
    for skill_data in skills_data:
        skill, is_new = Skill.objects.get_or_create(
            name=skill_data["name"],
            defaults={
                "type": skill_data["type"],
                "category": skill_data["category"],
            },
        )
        if is_new:
            created += 1
            ok(f"Skill cree: {skill.name}")
        else:
            skip(f"Skill existe deja: {skill.name}")

    print(f"\n  -> {created} nouvelles skills")


def seed_users():
    title("2. Creation des utilisateurs")

    created_users = []
    for payload in USER_FIXTURES:
        candidate_emails = [payload["email"], *payload.get("legacy_emails", [])]
        user = User.objects.filter(email__in=candidate_emails).first()
        if user:
            user.email = payload["email"]
            user.first_name = payload["first_name"]
            user.last_name = payload["last_name"]
            user.role = payload["role"]
            user.is_active = True
            user.is_staff = payload["role"] == User.Role.ADMIN
            user.set_password(payload["password"])
            user.save(
                update_fields=[
                    "email",
                    "first_name",
                    "last_name",
                    "role",
                    "is_active",
                    "is_staff",
                    "password",
                    "updated_at",
                ]
            )
            skip(f"User mis a jour: {payload['email']} / mot de passe: {payload['password']}")
            created_users.append(user)
            continue

        user = User.objects.create_user(
            email=payload["email"],
            password=payload["password"],
            first_name=payload["first_name"],
            last_name=payload["last_name"],
            role=payload["role"],
            is_staff=payload["role"] == User.Role.ADMIN,
        )
        ok(f"User cree: {user.email} / mot de passe: {payload['password']}")
        created_users.append(user)

    return created_users


def seed_profiles():
    title("3. Creation des profils")

    for payload in PROFILE_FIXTURES:
        try:
            user = User.objects.get(email__iexact=payload["email"])
        except User.DoesNotExist:
            err(f"User introuvable pour profil: {payload['email']}")
            continue

        profile, created = Profile.objects.get_or_create(user=user)
        profile.title = payload["title"]
        profile.bio = payload["bio"]
        profile.location = payload["location"]
        profile.experience_years = payload["experience_years"]
        profile.education_level = payload["education_level"]
        profile.phone = payload["phone"]
        profile.linkedin_url = payload["linkedin_url"]
        profile.save()
        if created:
            ok(f"Profil cree: {user.email}")
        else:
            skip(f"Profil mis a jour: {user.email}")


def seed_cvs():
    title("4. Creation des CV")

    for payload in CV_FIXTURES:
        try:
            user = User.objects.get(email__iexact=payload["email"])
        except User.DoesNotExist:
            err(f"User introuvable pour CV: {payload['email']}")
            continue

        cv = user.cvs.filter(is_active=True).order_by("-uploaded_at").first()
        if cv is None:
            cv = CV(user=user, is_active=True)

        cv.file_path = payload["file_path"]
        cv.file_type = payload["file_type"]
        cv.raw_text = payload["raw_text"]
        cv.is_active = True
        cv.save()
        ok(f"CV synchronise: {user.email}")


def seed_user_skills():
    title("5. Creation des skills utilisateurs")

    for payload in USER_SKILL_FIXTURES:
        try:
            user = User.objects.get(email__iexact=payload["email"])
        except User.DoesNotExist:
            err(f"User introuvable pour skills: {payload['email']}")
            continue

        expected_skill_names = {name.lower() for name, _level in payload["skills"]}
        for user_skill in UserSkill.objects.filter(user=user).select_related("skill"):
            if user_skill.skill.name.lower() not in expected_skill_names:
                user_skill.delete()

        created_count = 0
        for skill_name, level in payload["skills"]:
            skill = Skill.objects.filter(name__iexact=skill_name).first()
            if skill is None:
                err(f"Skill introuvable: {skill_name}")
                continue

            user_skill, created = UserSkill.objects.get_or_create(
                user=user,
                skill=skill,
                defaults={"level": level},
            )
            user_skill.level = level
            user_skill.save(update_fields=["level"])
            if created:
                created_count += 1

        ok(f"{user.email}: {created_count} nouvelles skills, relations synchronisees")


if __name__ == "__main__":
    print(f"\n{BOLD}{'=' * 50}")
    print("  SEED - Peuplement de la base de donnees")
    print(f"{'=' * 50}{RESET}")

    try:
        seed_skills()
        seed_users()
        seed_profiles()
        seed_cvs()
        seed_user_skills()

        print(f"\n{BOLD}{GREEN}{'=' * 50}")
        print("  Seed termine avec succes")
        print(f"{'=' * 50}{RESET}\n")

        print(f"  Skills     : {Skill.objects.count()}")
        print(f"  Users      : {User.objects.count()}")
        print(f"  Admins     : {User.objects.filter(role=User.Role.ADMIN).count()}")
        print(f"  Candidates : {User.objects.filter(role=User.Role.CANDIDATE).count()}")
        print(f"  Profiles   : {Profile.objects.count()}")
        print(f"  CVs        : {CV.objects.count()}")
        print(f"  UserSkills : {UserSkill.objects.count()}")
        print()
    except Exception as exc:
        print(f"\n{RED}ERREUR : {exc}{RESET}\n")
        raise
