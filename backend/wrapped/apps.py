from django.apps import AppConfig


class WrappedConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'wrapped'
    def ready(self):
        import wrapped.signals  # Import the file where your signal is defined