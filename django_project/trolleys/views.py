from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema, OpenApiRequest
from django.db.models import Q
from django.db import models

from .models import (
    Trolley, TrolleyLevel, Product, Specification, SpecificationItem,
    QRData, TrolleyDrawer, SensorData
)
from .serializers import (
    TrolleyListSerializer,
    TrolleyDetailSerializer,
    TrolleyCreateUpdateSerializer,
    TrolleyLevelSerializer,
    ProductSerializer,
    SpecificationSerializer,
    SpecificationDetailSerializer,
    SpecificationItemSerializer,
    QRDataSerializer,
    TrolleyDrawerSerializer,
    SensorDataSerializer,
)


class TrolleyViewSet(viewsets.ModelViewSet):
    """
    API para gestionar trolleys (carros de servicio) de aerolínea.

    Permite crear, actualizar, listar y eliminar trolleys, así como gestionar
    los niveles y drawers contenidos en cada trolley.

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
    queryset = Trolley.objects.prefetch_related('levels')

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

    @extend_schema(
        summary="Obtener contenido REQUERIDO del trolley",
        description="Obtiene todos los productos y cantidades que DEBE llevar este trolley según su especificación",
        parameters=[
            {
                'name': 'spec_id',
                'in': 'query',
                'description': 'ID de especificación (opcional)',
                'schema': {'type': 'string'}
            }
        ]
    )
    @action(detail=True, methods=['get'], url_path='required-contents')
    def get_required_contents(self, request, pk=None):
        """
        Obtener lo que DEBE llevar el trolley según la especificación.

        Devuelve todos los productos y cantidades que debe llevar este trolley
        basado en su especificación asociada.

        Query params:
        - spec_id: Filtrar por especificación específica (opcional)
        """
        trolley = self.get_object()
        spec_id = request.query_params.get('spec_id')

        # Si se proporciona un spec_id, filtrar por eso
        if spec_id:
            specifications = Specification.objects.filter(
                spec_id=spec_id,
                trolley_template=trolley
            )
        else:
            # Obtener todas las especificaciones donde este trolley es el template
            specifications = trolley.specifications.all() if hasattr(trolley, 'specifications') else Specification.objects.filter(trolley_template=trolley)

        if not specifications.exists():
            return Response({
                'trolley_id': trolley.id,
                'trolley_name': trolley.name,
                'message': 'No hay especificaciones asociadas a este trolley',
                'specifications': []
            })

        specs_data = []
        total_items = 0
        total_quantity = 0

        for spec in specifications:
            items = spec.items.select_related('product', 'drawer', 'drawer__level').all()

            items_by_drawer = {}
            items_by_level = {}
            spec_total_qty = 0

            for item in items:
                drawer_id = item.drawer.drawer_id
                level_number = item.drawer.level.level_number
                level_display = item.drawer.level.get_level_number_display()

                # Agrupar por drawer
                if drawer_id not in items_by_drawer:
                    items_by_drawer[drawer_id] = {
                        'drawer_id': drawer_id,
                        'drawer_level': level_display,
                        'products': []
                    }

                # Agrupar por nivel
                if level_number not in items_by_level:
                    items_by_level[level_number] = {
                        'level_number': level_number,
                        'level_display': level_display,
                        'products': []
                    }

                product_data = {
                    'product_id': item.product.id,
                    'product_name': item.product.name,
                    'sku': item.product.sku,
                    'category': item.product.category,
                    'required_quantity': item.required_quantity,
                    'price': float(item.product.price) if item.product.price else None,
                    'image': item.product.image_url
                }
                items_by_drawer[drawer_id]['products'].append(product_data)
                items_by_level[level_number]['products'].append(product_data)
                spec_total_qty += item.required_quantity
                total_quantity += item.required_quantity

            total_items += len(items)

            # Ordenar niveles por número
            levels_sorted = sorted(items_by_level.values(), key=lambda x: x['level_number'])

            specs_data.append({
                'spec_id': spec.spec_id,
                'spec_name': spec.name,
                'spec_description': spec.description,
                'total_items_count': len(items),
                'total_quantity': spec_total_qty,
                'by_level': levels_sorted,
                'by_drawer': list(items_by_drawer.values()),
            })

        return Response({
            'trolley_id': trolley.id,
            'trolley_name': trolley.name,
            'airline': trolley.airline,
            'total_specs': len(specs_data),
            'total_items': total_items,
            'total_quantity': total_quantity,
            'specifications': specs_data
        })

    @extend_schema(
        summary="Obtener contenido ACTUAL del trolley",
        description="Obtiene los productos detectados en cada drawer basado en las lecturas de sensores más recientes",
        parameters=[
            {
                'name': 'flight_number',
                'in': 'query',
                'description': 'Número de vuelo (opcional)',
                'schema': {'type': 'string'}
            },
            {
                'name': 'alert_flag',
                'in': 'query',
                'description': 'Filtrar por alertas: OK o Alert (opcional)',
                'schema': {'type': 'string', 'enum': ['OK', 'Alert']}
            }
        ]
    )
    @action(detail=True, methods=['get'], url_path='current-contents')
    def get_current_contents(self, request, pk=None):
        """
        Obtener lo que ACTUALMENTE tiene el trolley según los sensores.

        Devuelve los productos detectados en cada drawer basado en las lecturas
        más recientes de los sensores.

        Query params:
        - flight_number: Filtrar por vuelo específico (opcional)
        - alert_flag: Filtrar solo por alertas (OK o Alert) (opcional)
        """
        trolley = self.get_object()
        flight_number = request.query_params.get('flight_number')
        alert_flag = request.query_params.get('alert_flag')

        drawers = trolley.drawers.all()

        if not drawers.exists():
            return Response({
                'trolley_id': trolley.id,
                'trolley_name': trolley.name,
                'message': 'Este trolley no tiene drawers',
                'drawers': []
            })

        drawers_data = []
        total_sensor_readings = 0
        total_alerts = 0

        for drawer in drawers:
            sensor_data_qs = drawer.sensor_data.all().order_by('-timestamp')

            # Aplicar filtros
            if flight_number:
                sensor_data_qs = sensor_data_qs.filter(flight_number=flight_number)

            if alert_flag:
                sensor_data_qs = sensor_data_qs.filter(alert_flag=alert_flag)

            if sensor_data_qs.exists():
                # Agrupar por tipo de sensor y obtener el más reciente
                latest_readings = {}
                for sensor in sensor_data_qs:
                    key = (sensor.sensor_type, sensor.spec_id)
                    if key not in latest_readings:
                        latest_readings[key] = sensor

                readings = []
                for sensor in latest_readings.values():
                    readings.append({
                        'stream_id': sensor.stream_id,
                        'timestamp': sensor.timestamp,
                        'sensor_type': sensor.sensor_type,
                        'expected_value': sensor.expected_value,
                        'detected_value': sensor.detected_value,
                        'deviation_score': sensor.deviation_score,
                        'alert_flag': sensor.alert_flag,
                        'flight_number': sensor.flight_number,
                        'spec_id': sensor.spec_id,
                    })

                drawer_alerts = sum(1 for r in readings if r['alert_flag'] == 'Alert')
                total_sensor_readings += len(readings)
                total_alerts += drawer_alerts

                drawers_data.append({
                    'drawer_id': drawer.drawer_id,
                    'level': drawer.level.get_level_number_display(),
                    'readings_count': len(readings),
                    'alerts': drawer_alerts,
                    'sensor_readings': readings,
                })

        return Response({
            'trolley_id': trolley.id,
            'trolley_name': trolley.name,
            'airline': trolley.airline,
            'total_drawers': drawers.count(),
            'drawers_with_data': len(drawers_data),
            'total_sensor_readings': total_sensor_readings,
            'total_alerts': total_alerts,
            'drawers': drawers_data
        })


class TrolleyLevelViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar los niveles de los trolleys.

    Endpoints disponibles:
    - GET /levels/ - Listar todos los niveles
    - POST /levels/ - Crear un nuevo nivel
    - GET /levels/{id}/ - Obtener detalles de un nivel
    - PUT /levels/{id}/ - Actualizar un nivel
    - DELETE /levels/{id}/ - Eliminar un nivel
    """
    queryset = TrolleyLevel.objects.all()
    serializer_class = TrolleyLevelSerializer


class ProductViewSet(viewsets.ModelViewSet):
    """
    API para gestionar productos del catálogo.

    Permite crear, actualizar, listar, eliminar y buscar productos.
    Incluye funcionalidades de búsqueda avanzada, filtrado y operaciones
    de inventario como actualizar cantidad de stock.

    ## Acciones disponibles:

    - **list**: `GET /api/products/` - Listar productos (con filtros)
    - **create**: `POST /api/products/` - Crear nuevo producto
    - **retrieve**: `GET /api/products/{id}/` - Obtener detalles
    - **update**: `PUT /api/products/{id}/` - Actualizar producto
    - **partial_update**: `PATCH /api/products/{id}/` - Actualización parcial
    - **destroy**: `DELETE /api/products/{id}/` - Eliminar producto
    - **by_sku**: `GET /api/products/sku/{sku}/` - Buscar por SKU exacto
    - **search**: `GET /api/products/search/?query=term` - Búsqueda general
    - **update_stock**: `POST /api/products/{id}/update-stock/` - Actualizar stock

    ## Parámetros de filtrado:

    - `category`: Filtrar por categoría (ej: `?category=Bebida`)
    - `available`: Solo productos con stock (ej: `?available=true`)
    - `search`: Búsqueda en nombre, descripción y SKU (ej: `?search=agua`)

    ## Crear Producto:

    Con cURL: `curl -X POST http://localhost:8000/api/products/ -H "Content-Type: application/json" -d '{"name": "...", "sku": "...", "image_url": "https://..."}'`
    """
    queryset = Product.objects.all()
    serializer_class = ProductSerializer

    def get_queryset(self):
        """Filtrar productos según parámetros de búsqueda"""
        queryset = Product.objects.all()

        # Filtrar por categoría
        category = self.request.query_params.get('category')
        if category:
            queryset = queryset.filter(category__icontains=category)

        # Filtrar por disponibilidad (stock > 0)
        available = self.request.query_params.get('available')
        if available and available.lower() == 'true':
            queryset = queryset.filter(stock_quantity__gt=0)

        # Búsqueda general por nombre o descripción
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(description__icontains=search) |
                Q(sku__icontains=search)
            )

        return queryset

    @action(detail=False, methods=['get'], url_path='sku/(?P<sku>[^/.]+)')
    def by_sku(self, request, sku=None):
        """Obtener un producto por su SKU"""
        product = get_object_or_404(Product, sku=sku)
        serializer = self.get_serializer(product)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='search')
    def search(self, request):
        """Buscar productos por nombre, descripción o categoría"""
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'count': queryset.count(),
            'results': serializer.data
        })

    @action(detail=True, methods=['post'], url_path='update-stock')
    def update_stock(self, request, pk=None):
        """Actualizar el stock de un producto"""
        product = self.get_object()
        new_stock = request.data.get('stock_quantity')

        if new_stock is None:
            return Response(
                {'error': 'stock_quantity es requerido'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            product.stock_quantity = int(new_stock)
            if product.stock_quantity < 0:
                return Response(
                    {'error': 'El stock no puede ser negativo'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            product.save()
            serializer = self.get_serializer(product)
            return Response(serializer.data)
        except ValueError:
            return Response(
                {'error': 'stock_quantity debe ser un número entero'},
                status=status.HTTP_400_BAD_REQUEST
            )


class TrolleyDrawerViewSet(viewsets.ModelViewSet):
    """
    API para gestionar drawers de trolleys.

    Endpoints disponibles:
    - GET /api/drawers/ - Listar todos los drawers
    - POST /api/drawers/ - Crear un nuevo drawer
    - GET /api/drawers/{id}/ - Obtener detalles de un drawer
    - PUT /api/drawers/{id}/ - Actualizar un drawer
    - DELETE /api/drawers/{id}/ - Eliminar un drawer
    - GET /api/drawers/by-id/{drawer_id}/ - Obtener drawer por drawer_id (ej: DRW_013)
    - GET /api/drawers/{id}/sensor-data/ - Obtener lecturas de sensores de este drawer
    """
    queryset = TrolleyDrawer.objects.select_related('trolley', 'level')
    serializer_class = TrolleyDrawerSerializer

    @action(detail=False, methods=['get'], url_path='by-id/(?P<drawer_id>[^/.]+)')
    def by_drawer_id(self, request, drawer_id=None):
        """Obtener un drawer por su drawer_id (ej: DRW_013)"""
        drawer = get_object_or_404(TrolleyDrawer, drawer_id=drawer_id)
        serializer = self.get_serializer(drawer)
        return Response(serializer.data)

    @action(detail=True, methods=['get'], url_path='sensor-data')
    def get_sensor_data(self, request, pk=None):
        """Obtener todas las lecturas de sensores de este drawer"""
        drawer = self.get_object()
        sensor_data = drawer.sensor_data.all().order_by('-timestamp')

        # Permitir filtrado por alert_flag
        alert_flag = request.query_params.get('alert_flag')
        if alert_flag:
            sensor_data = sensor_data.filter(alert_flag=alert_flag)

        serializer = SensorDataSerializer(sensor_data, many=True)
        return Response({
            'drawer_id': drawer.drawer_id,
            'trolley_name': drawer.trolley.name,
            'count': sensor_data.count(),
            'results': serializer.data
        })


class SpecificationViewSet(viewsets.ModelViewSet):
    """
    API para gestionar especificaciones (planes de carga).

    Las especificaciones representan el plan detallado de qué productos
    deben ir en cada drawer de un trolley para un vuelo o servicio específico.

    Endpoints disponibles:
    - GET /api/specifications/ - Listar especificaciones
    - POST /api/specifications/ - Crear nueva especificación
    - GET /api/specifications/{id}/ - Obtener detalles
    - PUT /api/specifications/{id}/ - Actualizar
    - PATCH /api/specifications/{id}/ - Actualización parcial
    - DELETE /api/specifications/{id}/ - Eliminar
    - GET /api/specifications/{id}/items/ - Obtener items de la especificación
    - POST /api/specifications/{id}/items/ - Agregar item a la especificación
    """
    queryset = Specification.objects.prefetch_related('items__product', 'items__drawer')

    def get_serializer_class(self):
        """Retorna el serializer apropriado según la acción"""
        if self.action == 'retrieve':
            return SpecificationDetailSerializer
        return SpecificationSerializer

    @action(detail=True, methods=['get'], url_path='items')
    def get_items(self, request, pk=None):
        """Obtener todos los items de una especificación"""
        specification = self.get_object()
        items = specification.items.all()
        serializer = SpecificationItemSerializer(items, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], url_path='items')
    def add_item(self, request, pk=None):
        """Agregar un nuevo item a una especificación"""
        specification = self.get_object()
        data = request.data.copy()
        data['specification'] = specification.id
        serializer = SpecificationItemSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SpecificationItemViewSet(viewsets.ModelViewSet):
    """
    API para gestionar items de especificación.

    Los items de especificación conectan un producto específico con un drawer
    en una especificación determinada, incluyendo la cantidad requerida.

    Endpoints disponibles:
    - GET /api/specification-items/ - Listar todos los items
    - POST /api/specification-items/ - Crear nuevo item
    - GET /api/specification-items/{id}/ - Obtener detalles
    - PUT /api/specification-items/{id}/ - Actualizar
    - DELETE /api/specification-items/{id}/ - Eliminar
    """
    queryset = SpecificationItem.objects.select_related(
        'specification', 'product', 'drawer'
    )
    serializer_class = SpecificationItemSerializer


class SensorDataViewSet(viewsets.ModelViewSet):
    """
    API para gestionar datos de sensores en tiempo real.

    Endpoints disponibles:
    - GET /api/sensor-data/ - Listar todos los datos de sensores
    - POST /api/sensor-data/ - Crear un nuevo registro de sensor
    - GET /api/sensor-data/{id}/ - Obtener detalles de un registro
    - DELETE /api/sensor-data/{id}/ - Eliminar un registro
    - GET /api/sensor-data/by-drawer/{drawer_id}/ - Obtener sensores por drawer_id
    - GET /api/sensor-data/by-flight/{flight_number}/ - Obtener sensores por vuelo
    - GET /api/sensor-data/alerts/ - Obtener solo las alertas

    ## Parámetros de filtrado:

    - `alert_flag`: Filtrar por OK o Alert (ej: ?alert_flag=Alert)
    - `flight_number`: Filtrar por vuelo (ej: ?flight_number=QR117)
    - `sensor_type`: Filtrar por tipo de sensor (ej: ?sensor_type=camera)
    """
    queryset = SensorData.objects.select_related('drawer__trolley').order_by('-timestamp')
    serializer_class = SensorDataSerializer

    def get_queryset(self):
        """Filtrar sensores según parámetros de query"""
        queryset = SensorData.objects.select_related('drawer__trolley').order_by('-timestamp')

        # Filtrar por alert_flag
        alert_flag = self.request.query_params.get('alert_flag')
        if alert_flag:
            queryset = queryset.filter(alert_flag=alert_flag)

        # Filtrar por flight_number
        flight_number = self.request.query_params.get('flight_number')
        if flight_number:
            queryset = queryset.filter(flight_number=flight_number)

        # Filtrar por sensor_type
        sensor_type = self.request.query_params.get('sensor_type')
        if sensor_type:
            queryset = queryset.filter(sensor_type=sensor_type)

        # Filtrar por drawer_id
        drawer_id = self.request.query_params.get('drawer_id')
        if drawer_id:
            queryset = queryset.filter(drawer__drawer_id=drawer_id)

        return queryset

    @action(detail=False, methods=['get'], url_path='by-drawer/(?P<drawer_id>[^/.]+)')
    def by_drawer(self, request, drawer_id=None):
        """Obtener sensores por drawer_id"""
        sensor_data = SensorData.objects.filter(
            drawer__drawer_id=drawer_id
        ).select_related('drawer__trolley').order_by('-timestamp')

        if not sensor_data.exists():
            return Response(
                {'detail': f'No hay datos de sensores para el drawer {drawer_id}'},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = self.get_serializer(sensor_data, many=True)
        return Response({
            'drawer_id': drawer_id,
            'count': sensor_data.count(),
            'results': serializer.data
        })

    @action(detail=False, methods=['get'], url_path='by-flight/(?P<flight_number>[^/.]+)')
    def by_flight(self, request, flight_number=None):
        """Obtener sensores por flight_number"""
        sensor_data = SensorData.objects.filter(
            flight_number=flight_number
        ).select_related('drawer__trolley').order_by('-timestamp')

        if not sensor_data.exists():
            return Response(
                {'detail': f'No hay datos de sensores para el vuelo {flight_number}'},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = self.get_serializer(sensor_data, many=True)
        return Response({
            'flight_number': flight_number,
            'count': sensor_data.count(),
            'alerts': sensor_data.filter(alert_flag='Alert').count(),
            'results': serializer.data
        })

    @action(detail=False, methods=['get'], url_path='alerts')
    def get_alerts(self, request):
        """Obtener solo los registros con alertas"""
        sensor_data = SensorData.objects.filter(
            alert_flag='Alert'
        ).select_related('drawer__trolley').order_by('-timestamp')

        serializer = self.get_serializer(sensor_data, many=True)
        return Response({
            'total_alerts': sensor_data.count(),
            'results': serializer.data
        })


class QRDataViewSet(viewsets.ModelViewSet):
    """
    API para gestionar datos leídos desde QR.

    Endpoints disponibles:
    - GET /api/qr-data/ - Listar todos los datos QR (últimos primero)
    - POST /api/qr-data/ - Crear un nuevo registro QR
    - GET /api/qr-data/{id}/ - Obtener detalles de un registro QR
    - DELETE /api/qr-data/{id}/ - Eliminar un registro QR
    - GET /api/qr-data/latest/ - Obtener el último registro QR leído

    ## Crear QR Data:

    ```
    POST /api/qr-data/
    {
        "station_id": "PK02",
        "flight_number": "QR117",
        "customer_name": "Qatar Airways",
        "drawer_id": "DRW_013"
    }
    ```
    """
    queryset = QRData.objects.all()
    serializer_class = QRDataSerializer

    @action(detail=False, methods=['get'], url_path='latest')
    def get_latest(self, request):
        """Obtener el último registro QR leído"""
        latest_qr = QRData.objects.first()
        if latest_qr:
            serializer = self.get_serializer(latest_qr)
            return Response(serializer.data)
        return Response(
            {'detail': 'No hay datos QR registrados'},
            status=status.HTTP_404_NOT_FOUND
        )
