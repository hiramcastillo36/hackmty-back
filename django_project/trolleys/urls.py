from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    TrolleyViewSet,
    TrolleyLevelViewSet,
    ProductViewSet,
    SpecificationViewSet,
    SpecificationItemViewSet,
    QRDataViewSet,
    TrolleyDrawerViewSet,
    SensorDataViewSet,
)

# Crear el router y registrar los viewsets
router = DefaultRouter()
router.register(r'trolleys', TrolleyViewSet, basename='trolley')
router.register(r'levels', TrolleyLevelViewSet, basename='trolley-level')
router.register(r'products', ProductViewSet, basename='product')
router.register(r'specifications', SpecificationViewSet, basename='specification')
router.register(r'specification-items', SpecificationItemViewSet, basename='specification-item')
router.register(r'qr-data', QRDataViewSet, basename='qr-data')
router.register(r'drawers', TrolleyDrawerViewSet, basename='drawer')
router.register(r'sensor-data', SensorDataViewSet, basename='sensor-data')

urlpatterns = [
    path('', include(router.urls)),
]
