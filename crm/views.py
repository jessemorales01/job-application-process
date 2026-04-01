from rest_framework import viewsets, status, permissions
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.contrib.auth.models import User
from datetime import datetime, timedelta
from .models import Interaction, Stage, Application, JobOffer, Assessment, EmailAccount, AutoDetectedApplication
from .serializers import (
    UserSerializer,
    InteractionSerializer, StageSerializer, ApplicationSerializer, JobOfferSerializer, AssessmentSerializer,
    EmailAccountSerializer, AutoDetectedApplicationSerializer
)
from .mixins import CacheResponseMixin
from .cache_utils import CACHE_TTL
from .oauth_link import OAUTH_LINK_MAX_AGE, OAUTH_LINK_SALT


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

    def perform_destroy(self, instance):
        """
        Remove related auto-detected rows in one SQL DELETE (no per-row signals).

        CASCADE ORM delete would fire post_delete for each row; our handler
        runs broad Redis delete_pattern scans each time — requests appear to
        hang for large review queues.
        """
        from .cache_utils import invalidate_model_cache, invalidate_user_cache
        from .models import AutoDetectedApplication

        user_id = instance.user_id
        qs = AutoDetectedApplication.objects.filter(email_account=instance)
        qs._raw_delete(qs.db)

        invalidate_model_cache('auto_detected_applications')
        if user_id:
            invalidate_user_cache(user_id, 'auto_detected_applications')

        instance.delete()

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

    @action(detail=False, methods=['post'], url_path='sync')
    def sync(self, request):
        """Pull new messages from Gmail and create/update auto-detected applications."""
        from crm.services.email_sync_service import EmailSyncService

        raw = request.data.get('max_results', 100)
        try:
            max_results = int(raw)
        except (TypeError, ValueError):
            max_results = 100
        max_results = max(1, min(max_results, 500))

        accounts = list(self.get_queryset().filter(is_active=True))
        if not accounts:
            return Response(
                {
                    'detail': 'No active email account to sync.',
                    'accounts_processed': 0,
                    'total_emails_processed': 0,
                    'total_detected_created': 0,
                    'processing_errors': 0,
                    'errors': [],
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        service = EmailSyncService()
        summary = {
            'accounts_processed': 0,
            'total_emails_processed': 0,
            'total_detected_created': 0,
            'processing_errors': 0,
            'errors': [],
        }
        for account in accounts:
            try:
                result = service.sync_emails_for_account(
                    account, max_results=max_results
                )
                summary['accounts_processed'] += 1
                summary['total_emails_processed'] += result.get('processed', 0)
                summary['total_detected_created'] += result.get('created', 0)
                summary['processing_errors'] += int(result.get('errors') or 0)
            except Exception as e:
                summary['errors'].append(
                    {'email': account.email, 'error': str(e)}
                )
        return Response(summary, status=status.HTTP_200_OK)


@api_view(['GET'])
def initiate_oauth_flow(request):
    """Initiate Gmail OAuth flow and return authorization URL"""
    from django.core import signing
    from .services.gmail_oauth import GmailOAuthService

    try:
        service = GmailOAuthService()
        redirect_uri = request.query_params.get('redirect_uri')
        signed_state = signing.dumps(
            {'u': request.user.id},
            salt=OAUTH_LINK_SALT,
        )
        authorization_url, state = service.get_authorization_url(
            redirect_uri=redirect_uri,
            state=signed_state,
        )

        if hasattr(request, 'session'):
            request.session['oauth_state'] = state
            request.session['oauth_user_id'] = request.user.id
            request.session.save()

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
@permission_classes([AllowAny])  # Allow unauthenticated access for OAuth callback
def oauth_callback(request):
    """Handle OAuth callback and create/update email account"""
    from .services.gmail_oauth import GmailOAuthService
    from .models import EmailAccount
    from django.utils import timezone
    from django.http import HttpResponseRedirect
    
    authorization_code = request.query_params.get('code')
    state = request.query_params.get('state')
    redirect_uri = request.query_params.get('redirect_uri')
    
    if not authorization_code:
        # Redirect to frontend with error
        frontend_url = 'http://localhost:5173/settings?oauth_error=Authorization code is required'
        return HttpResponseRedirect(frontend_url)
    
    from django.core import signing
    from django.core.cache import cache

    user_id = None
    if state:
        try:
            payload = signing.loads(
                state,
                salt=OAUTH_LINK_SALT,
                max_age=OAUTH_LINK_MAX_AGE,
            )
            user_id = payload.get('u')
        except (signing.BadSignature, signing.SignatureExpired):
            user_id = None

    if user_id is None and state:
        user_id = cache.get(f'oauth_user_{state}')

    if user_id is None and hasattr(request, 'session'):
        stored_state = request.session.get('oauth_state')
        session_user_id = request.session.get('oauth_user_id')
        if session_user_id is not None and stored_state is not None:
            if state != stored_state:
                frontend_url = 'http://localhost:5173/settings?oauth_error=Invalid state parameter'
                return HttpResponseRedirect(frontend_url)
            user_id = session_user_id

    if not user_id:
        frontend_url = 'http://localhost:5173/settings?oauth_error=Session expired. Please try connecting again.'
        return HttpResponseRedirect(frontend_url)

    if state:
        cache.delete(f'oauth_user_{state}')
    
    try:
        # Get user
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            frontend_url = 'http://localhost:5173/settings?oauth_error=User not found'
            return HttpResponseRedirect(frontend_url)
        
        service = GmailOAuthService()
        token_data = service.handle_callback(
            authorization_code=authorization_code,
            redirect_uri=redirect_uri,
            state=state,
            authorization_response=request.build_absolute_uri(),
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
            user=user,
            defaults={
                'email': user.email or 'unknown@gmail.com',  # Will be updated from Gmail API later
                'provider': 'gmail',
                'access_token': token_data['access_token'],
                'refresh_token': token_data.get('refresh_token', ''),
                'token_expires_at': expires_at,
                'is_active': True,
            }
        )
        
        # Clear session data
        if hasattr(request, 'session'):
            request.session.pop('oauth_state', None)
            request.session.pop('oauth_user_id', None)
        
        # Redirect to frontend with success
        frontend_url = 'http://localhost:5173/settings?oauth_success=true'
        return HttpResponseRedirect(frontend_url)
        
    except Exception as e:
        # Redirect to frontend with error
        error_msg = str(e).replace(' ', '%20')
        frontend_url = f'http://localhost:5173/settings?oauth_error={error_msg}'
        return HttpResponseRedirect(frontend_url)


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


class AutoDetectedApplicationViewSet(CacheResponseMixin, viewsets.ModelViewSet):
    """ViewSet for AutoDetectedApplication CRUD operations"""
    queryset = AutoDetectedApplication.objects.select_related('email_account', 'email_account__user', 'merged_into_application').all()
    serializer_class = AutoDetectedApplicationSerializer
    cache_prefix = 'auto_detected_applications'
    cache_ttl = CACHE_TTL.get('auto_detected_applications', 300)  # 5 minutes default
    cache_user_specific = True

    def get_queryset(self):
        """Users can only see their own auto-detected applications"""
        qs = AutoDetectedApplication.objects.select_related(
            'email_account', 'email_account__user', 'merged_into_application'
        )
        
        if self.request.user.is_staff:
            return qs.all()

        # One JOIN; avoid a separate EmailAccount query per list request.
        qs = qs.filter(email_account__user=self.request.user)
        
        # Filter by status if provided
        status_filter = self.request.query_params.get('status', None)
        if status_filter:
            qs = qs.filter(status=status_filter)
        
        return qs
    
    @action(detail=True, methods=['post'])
    def accept(self, request, pk=None):
        """Accept detected application and create Application"""
        from django.utils import timezone
        
        detected_app = self.get_object()
        
        # Check if already reviewed
        if detected_app.status != 'pending':
            return Response(
                {'error': 'This detected application has already been reviewed.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get the first stage (for auto-assignment)
        first_stage = Stage.objects.order_by('order').first()
        if not first_stage:
            return Response(
                {'error': 'No stages exist. Please create a stage first.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create Application from detected item
        application_data = {
            'company_name': detected_app.company_name,
            'position': detected_app.position or '',
            'where_applied': detected_app.where_applied or '',
            'stage': first_stage,
            'created_by': request.user
        }
        
        # Allow custom fields to be overridden
        if 'salary_range' in request.data:
            application_data['salary_range'] = request.data['salary_range']
        if 'stack' in request.data:
            application_data['stack'] = request.data['stack']
        if 'email' in request.data:
            application_data['email'] = request.data['email']
        if 'phone_number' in request.data:
            application_data['phone_number'] = request.data['phone_number']
        if 'notes' in request.data:
            application_data['notes'] = request.data['notes']
        
        application = Application.objects.create(**application_data)
        
        # Update detected application
        detected_app.status = 'accepted'
        detected_app.merged_into_application = application
        detected_app.reviewed_at = timezone.now()
        detected_app.save()
        
        # Serialize response
        detected_serializer = self.get_serializer(detected_app)
        application_serializer = ApplicationSerializer(application)
        
        return Response({
            'application': application_serializer.data
        }, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """Reject detected application"""
        from django.utils import timezone
        
        detected_app = self.get_object()
        
        # Check if already reviewed
        if detected_app.status != 'pending':
            return Response(
                {'error': 'This detected application has already been reviewed.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Update status
        detected_app.status = 'rejected'
        detected_app.reviewed_at = timezone.now()
        detected_app.save()
        
        serializer = self.get_serializer(detected_app)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['post'])
    def merge(self, request, pk=None):
        """Merge detected application with existing Application"""
        from django.utils import timezone
        
        detected_app = self.get_object()
        
        # Check if already reviewed
        if detected_app.status != 'pending':
            return Response(
                {'error': 'This detected application has already been reviewed.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        raw_application_id = request.data.get('application_id')
        if raw_application_id is None or raw_application_id == '':
            return Response(
                {'application_id': 'This field is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        try:
            application_id = int(raw_application_id)
        except (TypeError, ValueError):
            return Response(
                {'application_id': 'A valid integer id is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        if application_id < 1:
            return Response(
                {'application_id': 'A valid integer id is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get application and verify user owns it
        try:
            application = Application.objects.select_related('created_by').get(id=application_id)
            
            # Check if user owns this application (unless staff)
            if not request.user.is_staff and application.created_by != request.user:
                return Response(
                    {'detail': 'Not found.'},
                    status=status.HTTP_404_NOT_FOUND
                )
        except Application.DoesNotExist:
            return Response(
                {'application_id': 'Application not found.'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Update detected application
        detected_app.status = 'merged'
        detected_app.merged_into_application = application
        detected_app.reviewed_at = timezone.now()
        detected_app.save()
        
        serializer = self.get_serializer(detected_app)
        return Response(serializer.data, status=status.HTTP_200_OK)

