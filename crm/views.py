from rest_framework import viewsets, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.contrib.auth.models import User
from .models import Customer, Contact, Interaction, Stage, Lead
from .serializers import (
    UserSerializer, CustomerSerializer, ContactSerializer,
    InteractionSerializer, StageSerializer, LeadSerializer
)


@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    """Register a new user"""
    serializer = UserSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CustomerViewSet(viewsets.ModelViewSet):
    """ViewSet for Customer CRUD operations"""
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def get_queryset(self):
        # Users can only see customers they created or all if staff
        if self.request.user.is_staff:
            return Customer.objects.all()
        return Customer.objects.filter(created_by=self.request.user)


class ContactViewSet(viewsets.ModelViewSet):
    """ViewSet for Contact CRUD operations"""
    queryset = Contact.objects.all()
    serializer_class = ContactSerializer

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def get_queryset(self):
        # Users can only see contacts they created or all if staff
        if self.request.user.is_staff:
            return Contact.objects.all()
        return Contact.objects.filter(created_by=self.request.user)


class InteractionViewSet(viewsets.ModelViewSet):
    """ViewSet for Interaction CRUD operations"""
    queryset = Interaction.objects.all()
    serializer_class = InteractionSerializer

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def get_queryset(self):
        # Users can only see interactions they created or all if staff
        if self.request.user.is_staff:
            return Interaction.objects.all()
        return Interaction.objects.filter(created_by=self.request.user)


class StageViewSet(viewsets.ModelViewSet):
    """API endpoint to view and edit Stages"""
    queryset = Stage.objects.all().order_by('order')
    serializer_class = StageSerializer

    def destroy(self, request, *args, **kwargs):
        """Prevent deletion if stage has leads"""
        stage = self.get_object()
        lead_count = stage.leads.count()
        
        if lead_count > 0:
            return Response(
                {"error": f"Cannot delete stage with {lead_count} lead(s). Move them to another stage first."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        return super().destroy(request, *args, **kwargs)


class LeadViewSet(viewsets.ModelViewSet):
    """ViewSet for Lead CRUD operations"""
    queryset = Lead.objects.select_related('stage', 'created_by').all()
    serializer_class = LeadSerializer

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def get_queryset(self):
        qs = Lead.objects.select_related('stage', 'created_by')
        if self.request.user.is_staff:
            return qs.all()
        return qs.filter(created_by=self.request.user)

