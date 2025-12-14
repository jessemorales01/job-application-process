from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    register, CustomerViewSet, ContactViewSet,
    InteractionViewSet, StageViewSet, LeadViewSet
)

router = DefaultRouter()
router.register(r'customers', CustomerViewSet)
router.register(r'contacts', ContactViewSet)
router.register(r'interactions', InteractionViewSet)
router.register(r'stages', StageViewSet)
router.register(r'leads', LeadViewSet)

urlpatterns = [
    path('register/', register, name='register'),
    path('', include(router.urls)),
]
