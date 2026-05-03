from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

class TestConnectionView(APIView):
    """
    Vue d'exemple pour tester la connexion entre React et Django via DRF.
    Vous pouvez utiliser cette structure pour vos futures APIs.
    """
    def get(self, request, *args, **kwargs):
        # Ici, vous pourriez interroger votre base de données avec des Models
        data = {
            "message": "Connexion réussie avec Django Rest Framework !",
            "status": "success",
            "info": "Le Backend est prêt à recevoir vos requêtes."
        }
        return Response(data, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        # Exemple de gestion d'une requête POST
        received_data = request.data
        return Response({
            "message": "Données reçues avec succès !",
            "your_data": received_data
        }, status=status.HTTP_201_CREATED)
