from rest_framework import viewsets, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.contrib.auth.models import User
from datetime import datetime, timedelta
from .models import Interaction, Stage, Application, JobOffer, Assessment, EmailAccount
from .serializers import (
    UserSerializer,
    InteractionSerializer, StageSerializer, ApplicationSerializer, JobOfferSerializer, AssessmentSerializer,
    EmailAccountSerializer
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


class EmailAccountViewSet(CacheResponseMixin, viewsets.ModelViewSet):
    """ViewSet for EmailAccount CRUD operations"""
    queryset = EmailAccount.objects.select_related('user').all()
    serializer_class = EmailAccountSerializer
    cache_prefix = 'email_accounts'
    cache_ttl = CACHE_TTL.get('email_accounts', 300)  # 5 minutes default
    cache_user_specific = True

    def perform_create(self, serializer):
        """Set the user to the current authenticated user"""
        serializer.save(user=self.request.user)

    def get_queryset(self):
        """Users can only see their own email account"""
        qs = EmailAccount.objects.select_related('user')
        if self.request.user.is_staff:
            return qs.all()
        return qs.filter(user=self.request.user)
    
    def list(self, request, *args, **kwargs):
        """Override list to handle OneToOne relationship"""
        queryset = self.filter_queryset(self.get_queryset())
        
        # For OneToOne, there's at most one account per user
        account = queryset.first()
        
        if account:
            serializer = self.get_serializer(account)
            return Response(serializer.data)
        else:
            # Return empty response (no account connected yet)
            return Response(None, status=status.HTTP_200_OK)
    
    def retrieve(self, request, *args, **kwargs):
        """Override retrieve to ensure user can only access their own account"""
        instance = self.get_object()
        
        # Check if user owns this account (unless staff)
        # instance.user is already loaded via select_related, no extra query
        if not request.user.is_staff and instance.user != request.user:
            return Response(
                {'detail': 'Not found.'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = self.get_serializer(instance)
        return Response(serializer.data)


@api_view(['GET'])
def initiate_oauth_flow(request):
    """Initiate Gmail OAuth flow and return authorization URL"""
    from .services.gmail_oauth import GmailOAuthService
    
    try:
        service = GmailOAuthService()
        redirect_uri = request.query_params.get('redirect_uri')
        authorization_url, state = service.get_authorization_url(redirect_uri=redirect_uri)
        
        # Store state in session for CSRF protection (optional)
        if hasattr(request, 'session'):
            request.session['oauth_state'] = state
        
        return Response({
            'authorization_url': authorization_url,
            'state': state
        }, status=status.HTTP_200_OK)
    except Exception as e:
        return Response(
            {'error': f'Failed to initiate OAuth flow: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
def oauth_callback(request):
    """Handle OAuth callback and create/update email account"""
    from .services.gmail_oauth import GmailOAuthService
    from .models import EmailAccount
    from django.utils import timezone
    
    authorization_code = request.query_params.get('code')
    state = request.query_params.get('state')
    redirect_uri = request.query_params.get('redirect_uri')
    
    if not authorization_code:
        return Response(
            {'code': 'Authorization code is required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        service = GmailOAuthService()
        token_data = service.handle_callback(
            authorization_code=authorization_code,
            redirect_uri=redirect_uri,
            state=state
        )
        
        # Parse expires_at
        expires_at = None
        if token_data.get('expires_at'):
            try:
                expires_at = datetime.fromisoformat(token_data['expires_at'].replace('Z', '+00:00'))
            except (ValueError, AttributeError):
                # If parsing fails, set to 1 hour from now
                expires_at = timezone.now() + timedelta(hours=1)
        
        # Get or create email account for user
        email_account, created = EmailAccount.objects.update_or_create(
            user=request.user,
            defaults={
                'email': request.user.email or 'unknown@gmail.com',  # Will be updated from Gmail API later
                'provider': 'gmail',
                'access_token': token_data['access_token'],
                'refresh_token': token_data.get('refresh_token', ''),
                'token_expires_at': expires_at,
                'is_active': True,
            }
        )
        
        return Response({
            'id': email_account.id,
            'email': email_account.email,
            'provider': email_account.provider,
            'is_active': email_account.is_active,
            'created': created
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response(
            {'error': f'Failed to handle OAuth callback: {str(e)}'},
            status=status.HTTP_400_BAD_REQUEST
        )


@api_view(['POST'])
def refresh_token(request, pk):
    """Refresh access token for email account"""
    from .services.gmail_oauth import GmailOAuthService
    from .models import EmailAccount
    from django.utils import timezone
    from datetime import timedelta
    
    try:
        # Get email account (with user scoping)
        email_account = EmailAccount.objects.select_related('user').get(pk=pk)
        
        # Check if user owns this account (unless staff)
        if not request.user.is_staff and email_account.user != request.user:
            return Response(
                {'detail': 'Not found.'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        service = GmailOAuthService()
        token_data = service.refresh_access_token(email_account)
        
        # Parse expires_at
        expires_at = None
        if token_data.get('expires_at'):
            try:
                expires_at = datetime.fromisoformat(token_data['expires_at'].replace('Z', '+00:00'))
            except (ValueError, AttributeError):
                expires_at = timezone.now() + timedelta(hours=1)
        
        # Update email account with new token
        email_account.access_token = token_data['access_token']
        if expires_at:
            email_account.token_expires_at = expires_at
        email_account.save()
        
        return Response({
            'access_token': '***',  # Don't expose token in response
            'expires_at': expires_at.isoformat() if expires_at else None,
            'message': 'Token refreshed successfully'
        }, status=status.HTTP_200_OK)
        
    except EmailAccount.DoesNotExist:
        return Response(
            {'detail': 'Not found.'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'error': f'Failed to refresh token: {str(e)}'},
            status=status.HTTP_400_BAD_REQUEST
        )

