from functools import lru_cache

import spacy
from spacy.matcher import PhraseMatcher

from data_engine.utils.text_utils import clean_text


SKILL_TERMS = [
    "python",
    "django",
    "react",
    "javascript",
    "sql",
    "mysql",
    "postgresql",
    "power bi",
    "tableau",
    "excel",
    "git",
    "docker",
    "linux",
    "tensorflow",
    "pytorch",
    "scikit learn",
    "scikit-learn",
    "machine learning",
    "deep learning",
    "nlp",
    "pandas",
    "numpy",
    "matplotlib",
    "autocad",
    "sketchup",
    "crm",
    "bureautique",
    "videosurveillance",
    "modelisation 3d",
    "genie electrique",
    "mecanique",
    "systemes mecaniques",
    "systemes electriques",
    "pneumatiques",
    "logistique",
    "transport",
    "vente",
    "commerce",
    "negociation",
    "relation client",
    "securite",
    "telesurveillance",
    "analyse",
    "francais",
    "arabe",
]

SKILL_LABELS = {
    "python": "Python",
    "django": "Django",
    "react": "React",
    "javascript": "JavaScript",
    "sql": "SQL",
    "mysql": "MySQL",
    "postgresql": "PostgreSQL",
    "power bi": "Power BI",
    "tableau": "Tableau",
    "excel": "Excel",
    "git": "Git",
    "docker": "Docker",
    "linux": "Linux",
    "tensorflow": "TensorFlow",
    "pytorch": "PyTorch",
    "scikit learn": "Scikit-learn",
    "scikit-learn": "Scikit-learn",
    "machine learning": "Machine Learning",
    "deep learning": "Deep Learning",
    "nlp": "NLP",
    "pandas": "Pandas",
    "numpy": "NumPy",
    "matplotlib": "Matplotlib",
    "autocad": "AutoCAD",
    "sketchup": "SketchUp",
    "crm": "CRM",
    "bureautique": "Bureautique",
    "videosurveillance": "Videosurveillance",
    "modelisation 3d": "Modelisation 3D",
    "genie electrique": "Genie electrique",
    "mecanique": "Mecanique",
    "systemes mecaniques": "Systemes mecaniques",
    "systemes electriques": "Systemes electriques",
    "pneumatiques": "Pneumatiques",
    "logistique": "Logistique",
    "transport": "Transport",
    "vente": "Vente",
    "commerce": "Commerce",
    "negociation": "Negociation",
    "relation client": "Relation client",
    "securite": "Securite",
    "telesurveillance": "Telesurveillance",
    "analyse": "Analyse",
    "francais": "Francais",
    "arabe": "Arabe",
}


@lru_cache(maxsize=1)
def get_nlp():
    return spacy.load("fr_core_news_sm")


@lru_cache(maxsize=1)
def get_matcher():
    nlp = get_nlp()
    matcher = PhraseMatcher(nlp.vocab, attr="LOWER")
    matcher.add("SKILLS", [nlp.make_doc(term) for term in SKILL_TERMS])
    return matcher


def extract_skills_from_text(text):
    text = clean_text(text)
    if not text:
        return []

    doc = get_nlp()(text)
    matches = get_matcher()(doc)

    labels = []
    for _, start, end in matches:
        key = doc[start:end].text.lower().strip()
        labels.append(SKILL_LABELS.get(key, doc[start:end].text.strip()))

    return list(dict.fromkeys(labels))


def serialize_skills(skills):
    return ", ".join(dict.fromkeys(skill for skill in skills if clean_text(skill)))
