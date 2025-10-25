from django.contrib import admin
from .models import Trolley, TrolleyLevel, TrolleyItem


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


class TrolleyItemInline(admin.TabularInline):
    model = TrolleyItem
    extra = 1
    fields = ('name', 'sku', 'quantity', 'category', 'price')


@admin.register(TrolleyLevel)
class TrolleyLevelAdmin(admin.ModelAdmin):
    list_display = ('trolley', 'level_number', 'capacity', 'created_at')
    list_filter = ('trolley', 'level_number')
    search_fields = ('trolley__name', 'description')
    readonly_fields = ('created_at', 'updated_at')
    inlines = [TrolleyItemInline]

    fieldsets = (
        ('Información General', {
            'fields': ('trolley', 'level_number', 'capacity', 'description')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(TrolleyItem)
class TrolleyItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'sku', 'quantity', 'category', 'price', 'level')
    list_filter = ('category', 'created_at', 'level__trolley')
    search_fields = ('name', 'sku', 'description')
    readonly_fields = ('created_at', 'updated_at', 'sku')

    fieldsets = (
        ('Información General', {
            'fields': ('level', 'name', 'description', 'category')
        }),
        ('Inventario', {
            'fields': ('sku', 'quantity', 'price')
        }),
        ('Media', {
            'fields': ('image',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
