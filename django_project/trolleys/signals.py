from django.db.models.signals import post_save
from django.dispatch import receiver
from django.forms.models import model_to_dict
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import json
from .models import QRData


@receiver(post_save, sender=QRData)
def qr_data_created(sender, instance, created, **kwargs):
    """
    Signal que se dispara cuando se crea un nuevo QRData.

    Envía un evento a todos los clientes WebSocket conectados.
    """
    if created:
        channel_layer = get_channel_layer()

        # Convertir el modelo a diccionario y serializar las fechas
        qr_data_dict = model_to_dict(instance)
        qr_data_dict['created_at'] = instance.created_at.isoformat()
        qr_data_dict['updated_at'] = instance.updated_at.isoformat()

        # Enviar el evento a todos los clientes en el grupo 'qr_data'
        async_to_sync(channel_layer.group_send)(
            'qr_data',
            {
                'type': 'qr_data_created',
                'data': qr_data_dict
            }
        )
