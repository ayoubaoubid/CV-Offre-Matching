from rest_framework import generics, status
from rest_framework.response import Response

from .models import JobOffer
from .serializers import JobOfferCreateSerializer, JobOfferSerializer


class JobOfferListCreateView(generics.ListCreateAPIView):
    queryset = JobOffer.objects.select_related("admin", "cluster").all()

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
