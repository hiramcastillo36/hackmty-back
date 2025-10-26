from django.db import models
from django.core.validators import MinValueValidator


class Trolley(models.Model):
    """Modelo para un trolley de aerolínea"""
    name = models.CharField(max_length=255, help_text="Nombre del trolley (ej: Trolley de Bebidas, Trolley de Comida)")
    description = models.TextField(blank=True, null=True, help_text="Descripción del trolley")
    airline = models.CharField(max_length=255, help_text="Aerolínea")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Trolley'
        verbose_name_plural = 'Trolleys'

    def __str__(self):
        return f"{self.name} - {self.airline}"


class TrolleyLevel(models.Model):
    """Modelo para los niveles/pisos de un trolley"""
    LEVEL_CHOICES = [
        (1, 'Nivel 1 (Superior)'),
        (2, 'Nivel 2 (Medio)'),
        (3, 'Nivel 3 (Inferior)'),
    ]

    trolley = models.ForeignKey(Trolley, on_delete=models.CASCADE, related_name='levels')
    level_number = models.IntegerField(choices=LEVEL_CHOICES, help_text="Número del nivel")
    capacity = models.IntegerField(default=20, help_text="Capacidad máxima de artículos en este nivel")
    description = models.TextField(blank=True, null=True, help_text="Descripción o notas del nivel")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('trolley', 'level_number')
        ordering = ['level_number']
        verbose_name = 'Nivel del Trolley'
        verbose_name_plural = 'Niveles del Trolley'

    def __str__(self):
        return f"{self.trolley.name} - {self.get_level_number_display()}"


class TrolleyItem(models.Model):
    """Modelo para artículos individuales en un nivel del trolley"""
    level = models.ForeignKey(TrolleyLevel, on_delete=models.CASCADE, related_name='items')
    name = models.CharField(max_length=255, help_text="Nombre del artículo")
    description = models.TextField(blank=True, null=True, help_text="Descripción del artículo")
    sku = models.CharField(
        max_length=100,
        unique=True,
        help_text="SKU único del artículo"
    )
    quantity = models.IntegerField(
        validators=[MinValueValidator(0)],
        help_text="Cantidad de unidades disponibles"
    )
    image = models.ImageField(
        upload_to='trolley_items/%Y/%m/%d/',
        null=True,
        blank=True,
        help_text="Imagen del artículo"
    )
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Precio del artículo"
    )
    category = models.CharField(
        max_length=100,
        blank=True,
        help_text="Categoría del artículo (ej: Bebida, Snack, Comida)"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['level', 'name']
        verbose_name = 'Artículo del Trolley'
        verbose_name_plural = 'Artículos del Trolley'
        indexes = [
            models.Index(fields=['sku']),
            models.Index(fields=['level']),
        ]

    def __str__(self):
        return f"{self.name} (SKU: {self.sku})"


class QRData(models.Model):
    """Modelo para datos leídos desde QR"""
    station_id = models.CharField(
        max_length=255,
        help_text="ID de la estación"
    )
    flight_number = models.CharField(
        max_length=255,
        help_text="Número de vuelo"
    )
    customer_name = models.CharField(
        max_length=255,
        help_text="Nombre del cliente/aerolínea"
    )
    drawer_id = models.CharField(
        max_length=255,
        help_text="ID del drawer/gaveta"
    )
    trolleys = models.ManyToManyField(
        Trolley,
        related_name='flights',
        help_text="Trolleys asignados a este vuelo"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Datos QR'
        verbose_name_plural = 'Datos QR'

    def __str__(self):
        return f"QR - {self.flight_number} - {self.station_id}"
