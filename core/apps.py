from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'
    verbose_name = 'College Portal Core'

    def ready(self):
        """Import signals when the app is ready."""
        try:
            import core.signals
        except ImportError:
            pass
