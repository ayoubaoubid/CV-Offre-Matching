# Guide : Connexion Frontend (React) ↔ Backend (Django)

Ce document sert de mémo pour comprendre comment envoyer des données depuis votre interface React et comment les réceptionner/sauvegarder avec Django.

---

## 1. Côté FRONTEND (React / Javascript)

Pour envoyer des données, on utilise l'instance `API` (Axios) que nous avons configurée dans `src/services/api.js`.

### Exemple d'envoi de formulaire
```javascript
import API from '../services/api';

// 1. Préparer les données du formulaire
const donneesFormulaire = {
    nom: "Dupont",
    email: "dupont@email.com",
    mot_de_passe: "123456"
};

// 2. Envoyer la requête POST au backend
// L'URL finale sera : http://127.0.0.1:8000/api/users/inscription/
API.post('/users/inscription/', donneesFormulaire)
  .then(response => {
      console.log("Succès ! Réponse du serveur :", response.data);
  })
  .catch(error => {
      console.error("Erreur lors de l'envoi :", error);
  });
```

---

## 2. Côté BACKEND (Django / Python)

Le backend suit un flux en 4 étapes pour traiter cette demande.

### Étape A : Le Modèle (`models.py`)
Définit la structure de la base de données.
```python
from django.db import models

class UserProfile(models.Model):
    nom = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    mot_de_passe = models.CharField(max_length=100)
```

### Étape B : Le Sérialiseur (`serializers.py`)
Traduit le JSON de React en objet Python et valide les données.
```python
from rest_framework import serializers
from .models import UserProfile

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ['nom', 'email', 'mot_de_passe']
```

### Étape C : La Vue (`views.py`)
Réceptionne la requête, utilise le sérialiseur et renvoie une réponse.
```python
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import UserProfileSerializer

class InscriptionView(APIView):
    def post(self, request):
        serializer = UserProfileSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save() # Sauvegarde en base de données
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
```

### Étape D : L'URL (`urls.py`)
Mappe le chemin vers la vue.
```python
from django.urls import path
from .views import InscriptionView

urlpatterns = [
    path('inscription/', InscriptionView.as_view(), name='inscription'),
]
```

---

## 3. Schéma du Flux de Données

1. **React** : `API.post('/chemin/', data)`
2. **Django URLs** : Reçoit l'appel et trouve la bonne `View`.
3. **Django Views** : Reçoit `request.data`.
4. **Django Serializers** : Vérifie si `nom`, `email`, etc., sont corrects.
5. **Django Models** : Enregistre dans la base de données (SQLite).
6. **Django Views** : Renvoie un message de succès (201 Created).
7. **React** : Reçoit la réponse dans le `.then()`.
