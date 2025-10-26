from django.contrib import admin
from .models import (
    Trolley, TrolleyLevel, TrolleyDrawer, Product,
    Specification, SpecificationItem, QRData, SensorData
)


@admin.register(Trolley)
class TrolleyAdmin(admin.ModelAdmin):
    list_display = ('name', 'airline', 'created_at')
    list_filter = ('airline', 'created_at')
    search_fields = ('name', 'airline')
    readonly_fields = ('created_at', 'updated_at')

    fieldsets = (
        ('Información General', {
            'fields': ('name', 'airline', 'description')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(TrolleyLevel)
class TrolleyLevelAdmin(admin.ModelAdmin):
    list_display = ('trolley', 'level_number', 'capacity', 'created_at')
    list_filter = ('trolley', 'level_number')
    search_fields = ('trolley__name', 'description')
    readonly_fields = ('created_at', 'updated_at')

    fieldsets = (
        ('Información General', {
            'fields': ('trolley', 'level_number', 'capacity', 'description')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(TrolleyDrawer)
class TrolleyDrawerAdmin(admin.ModelAdmin):
    list_display = ('drawer_id', 'trolley', 'level', 'created_at')
    list_filter = ('trolley', 'level', 'created_at')
    search_fields = ('drawer_id', 'trolley__name', 'description')
    readonly_fields = ('created_at', 'updated_at')

    fieldsets = (
        ('Información General', {
            'fields': ('drawer_id', 'trolley', 'level', 'description')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'sku', 'stock_quantity', 'category', 'price', 'created_at')
    list_filter = ('category', 'created_at')
    search_fields = ('name', 'sku', 'description')
    readonly_fields = ('created_at', 'updated_at')

    fieldsets = (
        ('Información General', {
            'fields': ('name', 'description', 'category')
        }),
        ('Inventario', {
            'fields': ('sku', 'stock_quantity', 'price')
        }),
        ('Media', {
            'fields': ('image',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


class SpecificationItemInline(admin.TabularInline):
    model = SpecificationItem
    extra = 1
    fields = ('drawer', 'product', 'required_quantity')


@admin.register(Specification)
class SpecificationAdmin(admin.ModelAdmin):
    list_display = ('spec_id', 'name', 'trolley_template', 'created_at')
    list_filter = ('trolley_template', 'created_at')
    search_fields = ('spec_id', 'name', 'description')
    readonly_fields = ('created_at', 'updated_at')
    inlines = [SpecificationItemInline]

    fieldsets = (
        ('Información General', {
            'fields': ('spec_id', 'name', 'description', 'trolley_template')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(SpecificationItem)
class SpecificationItemAdmin(admin.ModelAdmin):
    list_display = ('specification', 'drawer', 'product', 'required_quantity')
    list_filter = ('specification',)
    search_fields = ('specification__name', 'product__name', 'drawer__drawer_id')

    fieldsets = (
        ('Información General', {
            'fields': ('specification', 'drawer', 'product', 'required_quantity')
        }),
    )


@admin.register(QRData)
class QRDataAdmin(admin.ModelAdmin):
    list_display = ('flight_number', 'station_id', 'customer_name', 'drawer_id', 'created_at')
    list_filter = ('created_at', 'station_id')
    search_fields = ('flight_number', 'station_id', 'customer_name', 'drawer_id')
    readonly_fields = ('created_at', 'updated_at')

    fieldsets = (
        ('Información General', {
            'fields': ('station_id', 'flight_number', 'customer_name', 'drawer_id', 'trolleys')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(SensorData)
class SensorDataAdmin(admin.ModelAdmin):
    list_display = ('flight_number', 'stream_id', 'alert_flag', 'timestamp', 'created_at')
    list_filter = ('alert_flag', 'sensor_type', 'timestamp', 'created_at')
    search_fields = ('flight_number', 'stream_id', 'spec_id', 'customer_name')
    readonly_fields = ('created_at', 'updated_at', 'timestamp')

    fieldsets = (
        ('Información del Sensor', {
            'fields': ('stream_id', 'timestamp', 'sensor_type', 'spec_id')
        }),
        ('Ubicación', {
            'fields': ('station_id', 'drawer')
        }),
        ('Datos', {
            'fields': ('expected_value', 'detected_value', 'deviation_score')
        }),
        ('Vuelo', {
            'fields': ('flight_number', 'customer_name', 'operator_id')
        }),
        ('Alertas', {
            'fields': ('alert_flag',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
