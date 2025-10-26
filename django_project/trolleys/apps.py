from django.apps import AppConfig


class TrolleysConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'trolleys'
    verbose_name = 'Trolleys de Aerolínea'

    def ready(self):
        """Importar signals cuando la app se inicializa"""
        import trolleys.signals  # noqa
