# 🎓 Formation Complète : Projet CV-Offre-Matching

Bienvenue dans ce guide étape par étape. Nous allons construire ensemble le système de matching.

---

## PARTIE 1 — Django & Base de données

### 1. Structure d'un projet Django
- **`manage.py`** : Votre couteau suisse. Sert à lancer le serveur, faire les migrations, créer des admins.
- **`config/`** : Les réglages globaux (`settings.py`) et les routes principales (`urls.py`).
- **`apps/`** : Vos modules métier. Chaque app a son propre rôle.
  - `models.py` : Schéma de la base de données.
  - `views.py` : Logique qui reçoit les requêtes.
  - `serializers.py` : Transformation des données.

### 2. Créer des Modèles (`models.py`)
Dans `backend/apps/jobs/models.py`, définissons une offre d'emploi :
```python
from django.db import models

class JobOffer(models.Model):
    titre = models.CharField(max_length=200)
    entreprise = models.CharField(max_length=100)
    description = models.TextField()
    ville = models.CharField(max_length=100)
    competences_requises = models.TextField() # Stockées sous forme de texte séparé par des virgules
    date_publication = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.titre} - {self.entreprise}"
```

### 3. Migrations (SQLite → MySQL)
Chaque fois que vous changez `models.py`, vous devez :
1. `python manage.py makemigrations` : Django prépare le script SQL.
2. `python manage.py migrate` : Django exécute le script dans MySQL.
**Erreur à éviter** : Oublier de faire ces commandes après avoir ajouté un champ !

### 4. Utilisation de l'ORM (CRUD)
Ouvrez `python manage.py shell` pour tester :
```python
# Créer (Create)
JobOffer.objects.create(titre="Data Scientist", entreprise="OCP", description="...", ville="Casablanca")

# Lire (Read)
offres = JobOffer.objects.all()
offre_specifique = JobOffer.objects.get(id=1)

# Filtrer (Filter)
offres_casa = JobOffer.objects.filter(ville="Casablanca")
```

---

## PARTIE 2 — Django REST API

### 5. Les Serializers
Dans `backend/apps/jobs/serializers.py`, nous disons à Django comment transformer l'objet en JSON :
```python
from rest_framework import serializers
from .models import JobOffer

class JobOfferSerializer(serializers.ModelSerializer):
    class Meta:
        model = JobOffer
        fields = '__all__' # Expose tous les champs
```

### 6. Les Views & URLs
Dans `backend/apps/jobs/views.py` :
```python
from rest_framework import viewsets
from .models import JobOffer
from .serializers import JobOfferSerializer

class JobOfferViewSet(viewsets.ModelViewSet):
    queryset = JobOffer.objects.all()
    serializer_class = JobOfferSerializer
```

Puis dans `apps/jobs/urls.py` (comme nous l'avons configuré ensemble) :
```python
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import JobOfferViewSet

router = DefaultRouter()
router.register(r'offres', JobOfferViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
```

---

## PARTIE 3 — React Frontend

### 7. Appeler l'API avec Axios
Utilisez l'instance `API` que nous avons créée dans `src/services/api.js` :
```javascript
import API from '../services/api';

const fetchJobs = async () => {
    try {
        const response = await API.get('/jobs/offres/');
        console.log(response.data); // Liste des offres en JSON
    } catch (error) {
        console.error("Erreur de récupération", error);
    }
};
```

### 8. Afficher les données
```jsx
function JobList() {
  const [jobs, setJobs] = useState([]);

  useEffect(() => {
    API.get('/jobs/offres/').then(res => setJobs(res.data));
  }, []);

  return (
    <div>
      {jobs.map(job => (
        <div key={job.id}>
          <h3>{job.titre}</h3>
          <p>{job.entreprise} - {job.ville}</p>
        </div>
      ))}
    </div>
  );
}
```

### 13. Comment envoyer des données (Formulaires)
C'est le processus inverse : React envoie des données, Django les valide et MySQL les stocke.

#### A. Côté React : Le `API.post`
```jsx
const handleSubmit = async (e) => {
  e.preventDefault();
  try {
    // On envoie l'objet 'formData' au backend
    const response = await API.post('/jobs/offres/', formData);
    console.log("Sauvegardé !", response.data);
  } catch (error) {
    console.error("Erreur de sauvegarde", error.response.data);
  }
};
```

#### B. Côté Django : La magie du Serializer
Dans votre `ViewSet`, la méthode `create` est appelée automatiquement :
1. `serializer = JobOfferSerializer(data=request.data)` : Le traducteur prend les données.
2. `serializer.is_valid()` : Il vérifie si les champs obligatoires sont là.
3. `serializer.save()` : Il crée l'entrée dans la table MySQL.

---

## PARTIE 4 — Connexion Complète

### 9. Pourquoi CORS est important ?
Le navigateur bloque par sécurité les requêtes entre deux domaines différents (React sur le port 5173 et Django sur le port 8000). 
C'est pour cela que nous avons installé `django-cors-headers` et ajouté `CORS_ALLOW_ALL_ORIGINS = True`.

### 10. Exemple Bout-en-Bout
1. **Django** : Vous créez une offre via l'Admin Django.
2. **Base de données** : L'offre est stockée dans MySQL.
3. **API** : React appelle `/api/jobs/offres/`.
4. **React** : Le composant reçoit le JSON, met à jour son `state` et affiche l'offre à l'écran.

---

### 💡 Prochaine étape suggérée :
Voulez-vous que nous écrivions ensemble le premier modèle `Candidate` (Candidat) pour commencer à gérer l'importation de CV ?


# -------------------------------------------------------------
#  4. Structure des dossiers attendue dans backend/
# -------------------------------------------------------------
#
# backend/
# ├── config/
# │   ├── settings.py   ← INSTALLED_APPS = ['apps.users', 'apps.jobs', 'apps.matching']
# │   └── ...           ← AUTH_USER_MODEL = 'apps.users.User'  (pas 'users.User' !)
# ├── apps/
# │   ├── __init__.py   ← fichier vide obligatoire !
# │   ├── users/
# │   │   ├── __init__.py
# │   │   ├── apps.py   ← name = 'apps.users'
# │   │   └── models.py
# │   ├── jobs/
# │   │   ├── __init__.py
# │   │   ├── apps.py   ← name = 'apps.jobs'
# │   │   └── models.py ← from apps.users.models import ...
# │   └── matching/
# │       ├── __init__.py
# │       ├── apps.py   ← name = 'apps.matching'
# │       └── models.py ← from apps.users.models import ...
# │                        from apps.jobs.models import ...
# └── manage.py


# -------------------------------------------------------------
#  7. Commandes migrations — dans cet ordre EXACT
# -------------------------------------------------------------
#
#  python manage.py makemigrations user       # en premier (AUTH_USER_MODEL)
#  python manage.py makemigrations job        # dépend de user
#  python manage.py makemigrations matching   # dépend de user + job
#  python manage.py migrate                   # applique tout
#
#  python manage.py createsuperuser           # créer l'admin
#  python manage.py runserver                 # lancer le serveur
 
 
# -------------------------------------------------------------
#  8. Vérifier que les tables sont bien créées (PostgreSQL)
# -------------------------------------------------------------
#
#  psql -U postgres -d cv_matching_db
#  \dt          -- liste toutes les tables
#  \d users     -- détail de la table users
#  \d profiles
#  \d cvs
#  \d user_skills
#  \d skills
#  \d job_offers
#  \d job_skills
#  \d clusters
#  \d applications
#  \d notifications
#  \d search_history