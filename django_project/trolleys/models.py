from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


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


class TrolleyDrawer(models.Model):
    """Modelo para drawers/gavetas dentro de un trolley"""
    trolley = models.ForeignKey(Trolley, on_delete=models.CASCADE, related_name='drawers')
    drawer_id = models.CharField(
        max_length=255,
        unique=True,
        help_text="ID único del drawer (ej: DRW_013)"
    )
    level = models.ForeignKey(TrolleyLevel, on_delete=models.CASCADE, related_name='drawers')
    description = models.TextField(blank=True, null=True, help_text="Descripción o notas del drawer")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['trolley', 'drawer_id']
        verbose_name = 'Drawer del Trolley'
        verbose_name_plural = 'Drawers del Trolley'
        indexes = [
            models.Index(fields=['drawer_id']),
            models.Index(fields=['trolley']),
        ]

    def __str__(self):
        return f"{self.trolley.name} - {self.drawer_id}"


class Product(models.Model):
    """Catálogo maestro de todos los artículos/productos disponibles"""
    name = models.CharField(max_length=255, help_text="Nombre del artículo")
    description = models.TextField(blank=True, null=True, help_text="Descripción del artículo")
    sku = models.CharField(
        max_length=100,
        unique=True,
        help_text="SKU único del artículo (ej: DRK024, SNK082)"
    )
    stock_quantity = models.IntegerField(
        validators=[MinValueValidator(0)],
        default=0,
        help_text="Cantidad total de unidades en inventario"
    )
    image_url = models.URLField(
        null=True,
        blank=True,
        help_text="URL de la imagen del artículo"
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
        ordering = ['name']
        verbose_name = 'Producto'
        verbose_name_plural = 'Productos'
        indexes = [
            models.Index(fields=['sku']),
        ]

    def __str__(self):
        return f"{self.name} (SKU: {self.sku})"


class Specification(models.Model):
    """
    Representa el 'plan de carga' o 'receta' para un vuelo o tipo de servicio.
    Este modelo agrupa todos los artículos requeridos y coincide con el 'Spec_ID'
    de los datos del hackatón.
    """
    spec_id = models.CharField(
        max_length=255,
        unique=True,
        help_text="ID único de la especificación (ej: SPEC_20251013_01)"
    )
    name = models.CharField(
        max_length=255,
        help_text="Nombre descriptivo (ej: LX065 - Eco Bebidas, EK088 - Primera Clase)"
    )
    description = models.TextField(blank=True, null=True)
    trolley_template = models.ForeignKey(
        Trolley,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Trolley base para esta especificación"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Especificación'
        verbose_name_plural = 'Especificaciones'

    def __str__(self):
        return f"{self.name} ({self.spec_id})"


class SpecificationItem(models.Model):
    """
    Conecta una Especificación (el plan) con un Producto (qué)
    en un Drawer específico (dónde) y define la cantidad (cuánto).
    Esta es la "lista de empaque" que el sistema usará para validar.
    """
    specification = models.ForeignKey(
        Specification,
        on_delete=models.CASCADE,
        related_name='items',
        help_text="Especificación a la que pertenece este requisito"
    )
    drawer = models.ForeignKey(
        TrolleyDrawer,
        on_delete=models.CASCADE,
        related_name='spec_items',
        help_text="Drawer donde debe ir el producto"
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='spec_items',
        help_text="Producto requerido"
    )
    required_quantity = models.IntegerField(
        validators=[MinValueValidator(1)],
        help_text="Cantidad requerida de este producto en este drawer"
    )

    class Meta:
        unique_together = ('specification', 'drawer', 'product')
        ordering = ['specification', 'drawer']
        verbose_name = 'Artículo de Especificación'
        verbose_name_plural = 'Artículos de Especificación'

    def __str__(self):
        return f"{self.specification.name} -> {self.product.name} (x{self.required_quantity}) en {self.drawer.drawer_id}"


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


class SensorData(models.Model):
    """Modelo para datos leídos desde sensores en tiempo real"""
    SENSOR_TYPE_CHOICES = [
        ('camera', 'Cámara'),
        ('barcode', 'Código de Barras'),
        ('rfid', 'RFID'),
        ('scale', 'Báscula'),
        ('other', 'Otro'),
    ]

    ALERT_CHOICES = [
        ('OK', 'OK'),
        ('Alert', 'Alerta'),
    ]

    stream_id = models.CharField(max_length=255, help_text="ID del stream de datos")
    timestamp = models.DateTimeField(help_text="Tiempo exacto de la lectura")
    station_id = models.CharField(max_length=255, help_text="ID de la estación")
    drawer = models.ForeignKey(
        TrolleyDrawer,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sensor_data',
        help_text="Drawer del que proviene la lectura"
    )
    spec_id = models.CharField(max_length=255, help_text="ID de especificación")
    sensor_type = models.CharField(
        max_length=50,
        choices=SENSOR_TYPE_CHOICES,
        help_text="Tipo de sensor"
    )
    expected_value = models.CharField(
        max_length=255,
        blank=True,
        help_text="Valor esperado según especificación"
    )
    detected_value = models.CharField(
        max_length=255,
        blank=True,
        help_text="Valor detectado por el sensor"
    )
    deviation_score = models.FloatField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(1)],
        help_text="Puntuación de desviación (0-1)"
    )
    alert_flag = models.CharField(
        max_length=10,
        choices=ALERT_CHOICES,
        default='OK',
        help_text="Indicador de alerta"
    )
    operator_id = models.CharField(
        max_length=255,
        blank=True,
        help_text="ID del operador"
    )
    flight_number = models.CharField(
        max_length=255,
        help_text="Número de vuelo"
    )
    customer_name = models.CharField(
        max_length=255,
        help_text="Nombre del cliente/aerolínea"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Dato de Sensor'
        verbose_name_plural = 'Datos de Sensores'
        indexes = [
            models.Index(fields=['drawer']),
            models.Index(fields=['timestamp']),
            models.Index(fields=['flight_number']),
            models.Index(fields=['alert_flag']),
        ]

    def __str__(self):
        return f"{self.flight_number} - {self.stream_id} - {self.timestamp}"
