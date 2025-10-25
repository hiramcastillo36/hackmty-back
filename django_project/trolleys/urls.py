from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TrolleyViewSet, TrolleyLevelViewSet, TrolleyItemViewSet

# Crear el router y registrar los viewsets
router = DefaultRouter()
router.register(r'trolleys', TrolleyViewSet, basename='trolley')
router.register(r'levels', TrolleyLevelViewSet, basename='trolley-level')
router.register(r'items', TrolleyItemViewSet, basename='trolley-item')

urlpatterns = [
    path('', include(router.urls)),
]
