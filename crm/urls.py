from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    register,
    InteractionViewSet, StageViewSet, ApplicationViewSet, JobOfferViewSet, AssessmentViewSet,
    EmailAccountViewSet
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
    path('', include(router.urls)),
]
