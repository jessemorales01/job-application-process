from rest_framework import viewsets, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.contrib.auth.models import User
from .models import Interaction, Stage, Application, JobOffer, Assessment
from .serializers import (
    UserSerializer,
    InteractionSerializer, StageSerializer, ApplicationSerializer, JobOfferSerializer, AssessmentSerializer
)
from .mixins import CacheResponseMixin
from .cache_utils import CACHE_TTL


@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    """Register a new user"""
    serializer = UserSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class InteractionViewSet(CacheResponseMixin, viewsets.ModelViewSet):
    """ViewSet for Interaction CRUD operations"""
    queryset = Interaction.objects.select_related('application', 'created_by').all()
    serializer_class = InteractionSerializer
    cache_prefix = 'interactions'
    cache_ttl = CACHE_TTL['interactions']  # 5 minutes
    cache_user_specific = True

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def get_queryset(self):
        # Users can only see interactions they created or all if staff
        qs = Interaction.objects.select_related('application', 'created_by')
        if self.request.user.is_staff:
            return qs.all()
        return qs.filter(created_by=self.request.user)


class StageViewSet(CacheResponseMixin, viewsets.ModelViewSet):
    """API endpoint to view and edit Stages"""
    queryset = Stage.objects.all().order_by('order')
    serializer_class = StageSerializer
    cache_prefix = 'stages'
    cache_ttl = CACHE_TTL['stages']  # 24 hours - stages rarely change
    cache_user_specific = False  # Stages are shared across all users

    def destroy(self, request, *args, **kwargs):
        """Prevent deletion if stage has applications"""
        stage = self.get_object()
        application_count = stage.applications.count()
        
        if application_count > 0:
            return Response(
                {"error": f"Cannot delete stage with {application_count} application(s). Move them to another stage first."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        return super().destroy(request, *args, **kwargs)


class ApplicationViewSet(CacheResponseMixin, viewsets.ModelViewSet):
    """ViewSet for Application CRUD operations"""
    queryset = Application.objects.select_related('stage', 'created_by').all()
    serializer_class = ApplicationSerializer
    cache_prefix = 'applications'
    cache_ttl = CACHE_TTL['applications']  # 5 minutes
    cache_user_specific = True

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def get_queryset(self):
        qs = Application.objects.select_related('stage', 'created_by')
        if self.request.user.is_staff:
            return qs.all()
        return qs.filter(created_by=self.request.user)


class JobOfferViewSet(CacheResponseMixin, viewsets.ModelViewSet):
    """ViewSet for JobOffer CRUD operations"""
    queryset = JobOffer.objects.select_related('application', 'created_by').all()
    serializer_class = JobOfferSerializer
    cache_prefix = 'job_offers'
    cache_ttl = CACHE_TTL['job_offers']  # 5 minutes
    cache_user_specific = True

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def get_queryset(self):
        qs = JobOffer.objects.select_related('application', 'created_by')
        if self.request.user.is_staff:
            return qs.all()
        return qs.filter(created_by=self.request.user)


class AssessmentViewSet(CacheResponseMixin, viewsets.ModelViewSet):
    """ViewSet for Assessment CRUD operations"""
    queryset = Assessment.objects.select_related('created_by', 'application').all()
    serializer_class = AssessmentSerializer
    cache_prefix = 'assessments'
    cache_ttl = CACHE_TTL['assessments']  # 5 minutes
    cache_user_specific = True

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def get_queryset(self):
        qs = Assessment.objects.select_related('created_by', 'application')
        if self.request.user.is_staff:
            return qs.all()
        return qs.filter(created_by=self.request.user)

