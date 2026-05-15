from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import JobOffer, SavedJob
from .serializers import JobOfferCreateSerializer, JobOfferSerializer, SavedJobSerializer
from apps.users.views import get_current_user
from collections import Counter

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

class SaveJobView(APIView):

    def post(self, request, job_id):

        user = get_current_user(request)

        job = JobOffer.objects.get(pk=job_id)

        saved, created = SavedJob.objects.get_or_create(
            user=user,
            job=job
        )

        return Response({
            "saved": True,
            "created": created
        })

    def delete(self, request, job_id):

        user = get_current_user(request)

        job = JobOffer.objects.get(pk=job_id)

        SavedJob.objects.filter(
            user=user,
            job=job
        ).delete()

        return Response({
            "saved": False
        }, status=status.HTTP_204_NO_CONTENT)


class UserSavedJobsView(APIView):

    def get(self, request):

        user = get_current_user(request)

        jobs = SavedJob.objects.filter(user=user)

        serializer = SavedJobSerializer(jobs, many=True)

        return Response(serializer.data)

class JobsMapStatsView(APIView):

    def get(self, request):

        jobs = JobOffer.objects.all()

        city_counter = Counter()

        for job in jobs:
            city = job.localisation.strip().lower()

            if city:
                city_counter[city] += 1

        total = sum(city_counter.values())

        results = []

        for city, count in city_counter.items():

            results.append({
                "city": city,
                "count": count,
                "percent": round((count / total) * 100, 2)
            })

        return Response(results)