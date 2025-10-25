from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema, OpenApiRequest

from .models import Trolley, TrolleyLevel, TrolleyItem
from .serializers import (
    TrolleyListSerializer,
    TrolleyDetailSerializer,
    TrolleyCreateUpdateSerializer,
    TrolleyLevelSerializer,
    TrolleyItemSerializer,
)


class TrolleyViewSet(viewsets.ModelViewSet):
    """
    API para gestionar trolleys (carros de servicio) de aerolínea.

    Permite crear, actualizar, listar y eliminar trolleys, así como gestionar
    los niveles y artículos contenidos en cada trolley.

    ## Acciones disponibles:

    - **list**: `GET /api/trolleys/` - Listar todos los trolleys (paginado)
    - **create**: `POST /api/trolleys/` - Crear un nuevo trolley
    - **retrieve**: `GET /api/trolleys/{id}/` - Obtener detalles de un trolley
    - **update**: `PUT /api/trolleys/{id}/` - Actualizar un trolley
    - **partial_update**: `PATCH /api/trolleys/{id}/` - Actualización parcial
    - **destroy**: `DELETE /api/trolleys/{id}/` - Eliminar un trolley
    - **get_levels**: `GET /api/trolleys/{id}/levels/` - Listar niveles
    - **create_level**: `POST /api/trolleys/{id}/levels/` - Crear nuevo nivel
    - **statistics**: `GET /api/trolleys/{id}/stats/` - Estadísticas del trolley

    ## Parámetros de query:

    - `page`: Número de página (default: 1)
    - `page_size`: Resultados por página (default: 20)

    ## Ejemplo de uso:

    ```
    POST /api/trolleys/
    {
        "name": "Trolley de Bebidas",
        "airline": "Aeromexico",
        "description": "Carrito para bebidas"
    }
    ```
    """
    queryset = Trolley.objects.prefetch_related('levels__items')

    def get_serializer_class(self):
        """Retorna el serializer apropriado según la acción"""
        if self.action == 'retrieve':
            return TrolleyDetailSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return TrolleyCreateUpdateSerializer
        return TrolleyListSerializer

    @action(detail=True, methods=['get'], url_path='levels')
    def get_levels(self, request, pk=None):
        """Obtener todos los niveles de un trolley específico"""
        trolley = self.get_object()
        levels = trolley.levels.all()
        serializer = TrolleyLevelSerializer(levels, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], url_path='levels')
    def create_level(self, request, pk=None):
        """Crear un nuevo nivel para un trolley"""
        trolley = self.get_object()
        serializer = TrolleyLevelSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(trolley=trolley)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['get'], url_path='stats')
    def statistics(self, request, pk=None):
        """Obtener estadísticas del trolley"""
        trolley = self.get_object()
        levels = trolley.levels.all()

        stats = {
            'trolley_id': trolley.id,
            'trolley_name': trolley.name,
            'total_levels': levels.count(),
            'levels': []
        }

        total_items = 0
        total_quantity = 0

        for level in levels:
            items = level.items.all()
            level_quantity = sum(item.quantity for item in items)
            total_items += items.count()
            total_quantity += level_quantity

            stats['levels'].append({
                'level_number': level.level_number,
                'items_count': items.count(),
                'total_quantity': level_quantity,
                'capacity': level.capacity,
                'usage_percentage': round((level_quantity / level.capacity * 100) if level.capacity > 0 else 0, 2)
            })

        stats['total_items'] = total_items
        stats['total_quantity'] = total_quantity

        return Response(stats)


class TrolleyLevelViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar los niveles de los trolleys.

    Endpoints disponibles:
    - GET /levels/ - Listar todos los niveles
    - POST /levels/ - Crear un nuevo nivel
    - GET /levels/{id}/ - Obtener detalles de un nivel
    - PUT /levels/{id}/ - Actualizar un nivel
    - DELETE /levels/{id}/ - Eliminar un nivel
    - GET /levels/{id}/items/ - Listar artículos de un nivel
    - POST /levels/{id}/items/ - Agregar artículo a un nivel
    """
    queryset = TrolleyLevel.objects.prefetch_related('items')
    serializer_class = TrolleyLevelSerializer

    @action(detail=True, methods=['get'], url_path='items')
    def get_items(self, request, pk=None):
        """Obtener todos los artículos de un nivel"""
        level = self.get_object()
        items = level.items.all()
        serializer = TrolleyItemSerializer(items, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], url_path='items')
    def add_item(self, request, pk=None):
        """Agregar un nuevo artículo a un nivel"""
        level = self.get_object()
        serializer = TrolleyItemSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(level=level)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class TrolleyItemViewSet(viewsets.ModelViewSet):
    """
    API para gestionar artículos individuales en los trolleys.

    Permite crear, actualizar, listar, eliminar y buscar artículos.
    Incluye funcionalidades de búsqueda avanzada, filtrado y operaciones
    de inventario como actualizar cantidad o disminuir stock.

    ## Acciones disponibles:

    - **list**: `GET /api/items/` - Listar artículos (con filtros)
    - **create**: `POST /api/items/` - Crear nuevo artículo (con imagen opcional)
    - **retrieve**: `GET /api/items/{id}/` - Obtener detalles
    - **update**: `PUT /api/items/{id}/` - Actualizar artículo
    - **partial_update**: `PATCH /api/items/{id}/` - Actualización parcial
    - **destroy**: `DELETE /api/items/{id}/` - Eliminar artículo
    - **by_sku**: `GET /api/items/sku/{sku}/` - Buscar por SKU exacto
    - **search_items**: `GET /api/items/search/?query=term` - Búsqueda general
    - **update_quantity**: `POST /api/items/{id}/update-quantity/` - Actualizar cantidad
    - **decrease_quantity**: `POST /api/items/{id}/decrease-quantity/` - Disminuir stock

    ## Parámetros de filtrado:

    - `category`: Filtrar por categoría (ej: `?category=Bebida`)
    - `available`: Solo artículos disponibles (ej: `?available=true`)
    - `search`: Búsqueda en nombre, descripción y SKU (ej: `?search=agua`)

    ## Crear Item con Imagen:

    En Swagger: Selecciona un archivo en el campo "image"
    Con cURL: `curl -F "image=@archivo.jpg" ...`
    Con Python: `files={"image": open("archivo.jpg", "rb")}`

    Formatos soportados: JPG, PNG, GIF, WebP, BMP, TIFF
    """
    queryset = TrolleyItem.objects.all()
    serializer_class = TrolleyItemSerializer
    parser_classes = (MultiPartParser, FormParser)

    def get_queryset(self):
        """Filtrar artículos según parámetros de búsqueda"""
        queryset = TrolleyItem.objects.all()

        # Filtrar por categoría
        category = self.request.query_params.get('category')
        if category:
            queryset = queryset.filter(category__icontains=category)

        # Filtrar por disponibilidad (cantidad > 0)
        available = self.request.query_params.get('available')
        if available and available.lower() == 'true':
            queryset = queryset.filter(quantity__gt=0)

        # Búsqueda general por nombre o descripción
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                models.Q(name__icontains=search) |
                models.Q(description__icontains=search) |
                models.Q(sku__icontains=search)
            )

        return queryset

    @action(detail=False, methods=['get'], url_path='sku/(?P<sku>[^/.]+)')
    def by_sku(self, request, sku=None):
        """Obtener un artículo por su SKU"""
        item = get_object_or_404(TrolleyItem, sku=sku)
        serializer = self.get_serializer(item)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='search')
    def search_items(self, request):
        """Buscar artículos por nombre, descripción o categoría"""
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'count': queryset.count(),
            'results': serializer.data
        })

    @action(detail=True, methods=['post'], url_path='update-quantity')
    def update_quantity(self, request, pk=None):
        """Actualizar la cantidad de un artículo"""
        item = self.get_object()
        new_quantity = request.data.get('quantity')

        if new_quantity is None:
            return Response(
                {'error': 'quantity es requerido'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            item.quantity = int(new_quantity)
            if item.quantity < 0:
                return Response(
                    {'error': 'La cantidad no puede ser negativa'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            item.save()
            serializer = self.get_serializer(item)
            return Response(serializer.data)
        except ValueError:
            return Response(
                {'error': 'quantity debe ser un número entero'},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['post'], url_path='decrease-quantity')
    def decrease_quantity(self, request, pk=None):
        """Disminuir la cantidad de un artículo"""
        item = self.get_object()
        amount = request.data.get('amount', 1)

        try:
            amount = int(amount)
            if amount < 0:
                return Response(
                    {'error': 'El monto debe ser positivo'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if item.quantity < amount:
                return Response(
                    {'error': f'No hay suficiente cantidad. Disponible: {item.quantity}'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            item.quantity -= amount
            item.save()
            serializer = self.get_serializer(item)
            return Response(serializer.data)
        except ValueError:
            return Response(
                {'error': 'amount debe ser un número entero'},
                status=status.HTTP_400_BAD_REQUEST
            )


# Importar Q y models para las búsquedas
from django.db.models import Q
from django.db import models
