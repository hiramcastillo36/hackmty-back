import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
from django.forms.models import model_to_dict
from .models import QRData

logger = logging.getLogger(__name__)


class QRDataConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer para QRData.

    Maneja conexiones y envía actualizaciones en tiempo real cuando se crea un nuevo QRData.
    """

    async def connect(self):
        """Se ejecuta cuando un cliente se conecta al WebSocket"""
        self.group_name = 'qr_data'

        # Agregar el grupo de canal
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )

        await self.accept()
        logger.info(f"Cliente WebSocket conectado: {self.channel_name}")

    async def disconnect(self, close_code):
        """Se ejecuta cuando un cliente se desconecta"""
        # Remover del grupo de canal
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )
        print(f"Cliente desconectado: {self.channel_name}")

    async def qr_data_created(self, event):
        """
        Se ejecuta cuando se recibe un evento 'qr_data_created' del grupo.
        Este método es llamado automáticamente por Channels cuando se envía
        un mensaje al grupo con el nombre 'qr_data_created'.
        """
        # Enviar los datos del QR al cliente
        await self.send(text_data=json.dumps({
            'type': 'qr_data_created',
            'data': event['data']
        }))

    async def receive(self, text_data):
        """
        Se ejecuta cuando el cliente envía un mensaje.
        Opcional: útil para manejar mensajes del cliente al servidor.
        """
        try:
            data = json.loads(text_data)

            # Aquí puedes manejar diferentes tipos de mensajes del cliente
            if data.get('action') == 'get_latest':
                latest_qr = await self.get_latest_qr()
                await self.send(text_data=json.dumps({
                    'type': 'latest_qr',
                    'data': latest_qr
                }))
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'error': 'Formato JSON inválido'
            }))

    @sync_to_async
    def get_latest_qr(self):
        """Obtiene el último QRData registrado"""
        try:
            latest = QRData.objects.order_by('-created_at').first()
            if latest:
                qr_dict = model_to_dict(latest)
                # Serializar fechas al formato ISO
                qr_dict['created_at'] = latest.created_at.isoformat()
                qr_dict['updated_at'] = latest.updated_at.isoformat()
                return qr_dict
            return None
        except Exception as e:
            print(f"Error obteniendo último QRData: {e}")
            return None
