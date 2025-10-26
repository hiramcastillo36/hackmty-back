from django.db import models
from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field
from drf_spectacular.types import OpenApiTypes
from .models import (
    Trolley, TrolleyLevel, Product, Specification, SpecificationItem,
    QRData, TrolleyDrawer, SensorData
)


class ProductSerializer(serializers.ModelSerializer):
    """
    Serializer para productos del catálogo.

    Permite crear y actualizar productos con URL de imagen.
    """

    class Meta:
        model = Product
        fields = [
            'id',
            'name',
            'description',
            'sku',
            'stock_quantity',
            'image_url',
            'price',
            'category',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at', 'id']


class TrolleyLevelSerializer(serializers.ModelSerializer):
    """Serializer para los niveles del trolley"""
    level_display = serializers.SerializerMethodField()

    class Meta:
        model = TrolleyLevel
        fields = [
            'id',
            'trolley',
            'level_number',
            'level_display',
            'capacity',
            'description',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at', 'id']

    def get_level_display(self, obj):
        """Retorna el nombre legible del nivel"""
        return obj.get_level_number_display()


class TrolleyDetailSerializer(serializers.ModelSerializer):
    """Serializer detallado del trolley con todos sus niveles"""
    levels = TrolleyLevelSerializer(many=True, read_only=True)

    class Meta:
        model = Trolley
        fields = [
            'id',
            'name',
            'description',
            'airline',
            'levels',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at', 'id']


class TrolleyListSerializer(serializers.ModelSerializer):
    """Serializer simple para listar trolleys"""
    level_count = serializers.SerializerMethodField()

    class Meta:
        model = Trolley
        fields = [
            'id',
            'name',
            'airline',
            'level_count',
            'created_at',
        ]
        read_only_fields = ['created_at', 'id']

    def get_level_count(self, obj):
        """Retorna la cantidad de niveles"""
        return obj.levels.count()


class TrolleyCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer para crear y actualizar trolleys"""

    class Meta:
        model = Trolley
        fields = [
            'name',
            'description',
            'airline',
        ]


class QRDataSerializer(serializers.ModelSerializer):
    """Serializer para datos del QR"""
    trolleys = TrolleyListSerializer(many=True, read_only=True)
    trolley_ids = serializers.PrimaryKeyRelatedField(
        queryset=Trolley.objects.all(),
        many=True,
        write_only=True,
        required=False,
        source='trolleys'
    )

    class Meta:
        model = QRData
        fields = [
            'id',
            'station_id',
            'flight_number',
            'customer_name',
            'drawer_id',
            'trolleys',
            'trolley_ids',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at', 'id', 'trolleys']


class TrolleyDrawerSerializer(serializers.ModelSerializer):
    """Serializer para drawers del trolley"""
    trolley_name = serializers.CharField(source='trolley.name', read_only=True)
    level_display = serializers.CharField(source='level.get_level_number_display', read_only=True)

    class Meta:
        model = TrolleyDrawer
        fields = [
            'id',
            'trolley',
            'trolley_name',
            'drawer_id',
            'level',
            'level_display',
            'description',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at', 'id']


class SensorDataSerializer(serializers.ModelSerializer):
    """Serializer para datos de sensores"""
    drawer_info = TrolleyDrawerSerializer(source='drawer', read_only=True)
    trolley_name = serializers.SerializerMethodField()

    class Meta:
        model = SensorData
        fields = [
            'id',
            'stream_id',
            'timestamp',
            'station_id',
            'drawer',
            'drawer_info',
            'spec_id',
            'sensor_type',
            'expected_value',
            'detected_value',
            'deviation_score',
            'alert_flag',
            'operator_id',
            'flight_number',
            'customer_name',
            'trolley_name',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at', 'id']

    def get_trolley_name(self, obj):
        """Obtiene el nombre del trolley si existe"""
        if obj.drawer:
            return obj.drawer.trolley.name
        return None


class SpecificationItemSerializer(serializers.ModelSerializer):
    """Serializer para items de especificación"""
    product_info = ProductSerializer(source='product', read_only=True)
    drawer_info = TrolleyDrawerSerializer(source='drawer', read_only=True)

    class Meta:
        model = SpecificationItem
        fields = [
            'id',
            'specification',
            'drawer',
            'drawer_info',
            'product',
            'product_info',
            'required_quantity',
        ]
        read_only_fields = ['id']


class SpecificationSerializer(serializers.ModelSerializer):
    """Serializer para especificaciones (planes de carga)"""
    items = SpecificationItemSerializer(many=True, read_only=True)
    trolley_template_name = serializers.CharField(
        source='trolley_template.name',
        read_only=True
    )

    class Meta:
        model = Specification
        fields = [
            'id',
            'spec_id',
            'name',
            'description',
            'trolley_template',
            'trolley_template_name',
            'items',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at', 'id']


class SpecificationDetailSerializer(serializers.ModelSerializer):
    """Serializer detallado para especificaciones con todos sus items"""
    items = SpecificationItemSerializer(many=True, read_only=True)
    trolley_info = serializers.SerializerMethodField()

    class Meta:
        model = Specification
        fields = [
            'id',
            'spec_id',
            'name',
            'description',
            'trolley_template',
            'trolley_info',
            'items',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at', 'id']

    def get_trolley_info(self, obj):
        """Retorna información detallada del trolley template"""
        if obj.trolley_template:
            return TrolleyDetailSerializer(obj.trolley_template).data
        return None


class TrolleyRequiredContentsSerializer(serializers.Serializer):
    """
    Serializer para la respuesta de lo que DEBE llevar un trolley.

    Estructura de respuesta que agrupa los productos requeridos por especificación
    y luego por drawer.
    """
    trolley_id = serializers.IntegerField()
    trolley_name = serializers.CharField()
    airline = serializers.CharField()
    total_specs = serializers.IntegerField()
    total_items = serializers.IntegerField()
    total_quantity = serializers.IntegerField()
    specifications = serializers.ListField()


class TrolleyCurrentContentsSerializer(serializers.Serializer):
    """
    Serializer para la respuesta de lo que ACTUALMENTE tiene un trolley.

    Estructura de respuesta basada en lecturas de sensores más recientes.
    """
    trolley_id = serializers.IntegerField()
    trolley_name = serializers.CharField()
    airline = serializers.CharField()
    total_drawers = serializers.IntegerField()
    drawers_with_data = serializers.IntegerField()
    total_sensor_readings = serializers.IntegerField()
    total_alerts = serializers.IntegerField()
    drawers = serializers.ListField()



