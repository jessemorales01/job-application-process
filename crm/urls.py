from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    register,
    InteractionViewSet, StageViewSet, ApplicationViewSet, JobOfferViewSet, AssessmentViewSet,
    EmailAccountViewSet, initiate_oauth_flow, oauth_callback, refresh_token
)

router = DefaultRouter()
router.register(r'interactions', InteractionViewSet)
router.register(r'stages', StageViewSet)
router.register(r'applications', ApplicationViewSet)
router.register(r'job-offers', JobOfferViewSet)
router.register(r'assessments', AssessmentViewSet)
router.register(r'email-accounts', EmailAccountViewSet)

urlpatterns = [
    path('register/', register, name='register'),
    path('email-accounts/oauth/initiate/', initiate_oauth_flow, name='oauth-initiate'),
    path('email-accounts/oauth/callback/', oauth_callback, name='oauth-callback'),
    path('email-accounts/<int:pk>/refresh-token/', refresh_token, name='refresh-token'),
    path('', include(router.urls)),
]
