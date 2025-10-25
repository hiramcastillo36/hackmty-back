from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status
from .models import Trolley, TrolleyLevel, TrolleyItem


class TrolleyAPITestCase(TestCase):
    """Tests para la API de Trolleys"""

    def setUp(self):
        """Configurar datos de prueba"""
        self.client = APIClient()

        # Crear un trolley
        self.trolley = Trolley.objects.create(
            name='Trolley de Prueba',
            description='Trolley para testing',
            airline='Test Airline'
        )

        # Crear un nivel
        self.level = TrolleyLevel.objects.create(
            trolley=self.trolley,
            level_number=1,
            capacity=20,
            description='Nivel 1'
        )

        # Crear un artículo
        self.item = TrolleyItem.objects.create(
            level=self.level,
            name='Agua',
            sku='SKU-001',
            quantity=10,
            price='2.50',
            category='Bebida'
        )

    def test_create_trolley(self):
        """Probar creación de trolley"""
        data = {
            'name': 'Trolley Nueva',
            'airline': 'Aeromexico',
            'description': 'Nueva descripción'
        }
        response = self.client.post('/api/trolleys/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_list_trolleys(self):
        """Probar listado de trolleys"""
        response = self.client.get('/api/trolleys/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)

    def test_retrieve_trolley(self):
        """Probar obtener detalles de trolley"""
        response = self.client.get(f'/api/trolleys/{self.trolley.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Trolley de Prueba')

    def test_update_trolley(self):
        """Probar actualización de trolley"""
        data = {
            'name': 'Trolley Actualizado',
            'airline': 'Aeromexico',
            'description': 'Descripción actualizada'
        }
        response = self.client.put(
            f'/api/trolleys/{self.trolley.id}/',
            data,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_delete_trolley(self):
        """Probar eliminación de trolley"""
        response = self.client.delete(f'/api/trolleys/{self.trolley.id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_get_trolley_levels(self):
        """Probar obtener niveles de trolley"""
        response = self.client.get(f'/api/trolleys/{self.trolley.id}/levels/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_create_level(self):
        """Probar creación de nivel"""
        data = {
            'level_number': 2,
            'capacity': 25,
            'description': 'Nivel 2'
        }
        response = self.client.post(
            f'/api/trolleys/{self.trolley.id}/levels/',
            data,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_get_trolley_statistics(self):
        """Probar estadísticas de trolley"""
        response = self.client.get(f'/api/trolleys/{self.trolley.id}/stats/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['trolley_id'], self.trolley.id)
        self.assertEqual(response.data['total_items'], 1)

    def test_list_items(self):
        """Probar listado de artículos"""
        response = self.client.get('/api/items/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)

    def test_retrieve_item(self):
        """Probar obtener detalles de artículo"""
        response = self.client.get(f'/api/items/{self.item.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Agua')

    def test_search_by_sku(self):
        """Probar búsqueda por SKU"""
        response = self.client.get('/api/items/sku/SKU-001/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Agua')

    def test_search_items(self):
        """Probar búsqueda de artículos"""
        response = self.client.get('/api/items/search/?query=agua')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)

    def test_filter_by_category(self):
        """Probar filtrado por categoría"""
        response = self.client.get('/api/items/?category=Bebida')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_filter_available_items(self):
        """Probar filtrado de artículos disponibles"""
        response = self.client.get('/api/items/?available=true')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_update_quantity(self):
        """Probar actualización de cantidad"""
        data = {'quantity': 15}
        response = self.client.post(
            f'/api/items/{self.item.id}/update-quantity/',
            data,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['quantity'], 15)

    def test_decrease_quantity(self):
        """Probar disminución de cantidad"""
        data = {'amount': 3}
        response = self.client.post(
            f'/api/items/{self.item.id}/decrease-quantity/',
            data,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['quantity'], 7)

    def test_decrease_quantity_insufficient(self):
        """Probar disminución con cantidad insuficiente"""
        data = {'amount': 20}
        response = self.client.post(
            f'/api/items/{self.item.id}/decrease-quantity/',
            data,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
