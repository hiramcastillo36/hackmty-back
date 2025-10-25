from django.db import models
from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field
from drf_spectacular.types import OpenApiTypes
from .models import Trolley, TrolleyLevel, TrolleyItem


class TrolleyItemSerializer(serializers.ModelSerializer):
    """
    Serializer para artículos del trolley.

    Permite crear y actualizar items con imágenes.
    """
    # Especificar que 'image' es un archivo para Swagger
    image = serializers.ImageField(
        required=False,
        allow_null=True,
        help_text="Imagen del artículo (JPG, PNG, GIF, WebP, etc)"
    )

    class Meta:
        model = TrolleyItem
        fields = [
            'id',
            'level',
            'name',
            'description',
            'sku',
            'quantity',
            'image',
            'price',
            'category',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at', 'id']

    def to_representation(self, instance):
        """Retornar URL completa de la imagen en respuestas"""
        representation = super().to_representation(instance)
        # Si hay imagen, asegurarse que la URL sea accesible
        if representation['image']:
            request = self.context.get('request')
            if request and not representation['image'].startswith('http'):
                representation['image'] = request.build_absolute_uri(representation['image'])
        return representation


class TrolleyLevelSerializer(serializers.ModelSerializer):
    """Serializer para los niveles del trolley con sus artículos"""
    items = TrolleyItemSerializer(many=True, read_only=True)
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
            'items',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at', 'id']

    def get_level_display(self, obj):
        """Retorna el nombre legible del nivel"""
        return obj.get_level_number_display()


class TrolleyDetailSerializer(serializers.ModelSerializer):
    """Serializer detallado del trolley con todos sus niveles e items"""
    levels = TrolleyLevelSerializer(many=True, read_only=True)
    total_items = serializers.SerializerMethodField()

    class Meta:
        model = Trolley
        fields = [
            'id',
            'name',
            'description',
            'airline',
            'levels',
            'total_items',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at', 'id']

    def get_total_items(self, obj):
        """Cuenta el total de artículos en todos los niveles"""
        total = 0
        for level in obj.levels.all():
            total += level.items.aggregate(
                total_qty=models.Sum('quantity')
            )['total_qty'] or 0
        return total


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

    

