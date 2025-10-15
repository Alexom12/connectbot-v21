from django.apps import AppConfig


class BotsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'bots'

    def ready(self):
        # Initialize module-level singleton MatchingServiceClient so that
        # in-memory metrics are available from the moment the Django app
        # registry is ready. Any failure here should be logged but must not
        # crash the application startup.
        try:
            from .services.matching_service_client import get_default_client
            get_default_client()
        except Exception as e:
            import logging
            logging.getLogger(__name__).exception('Failed to initialize MatchingServiceClient in AppConfig.ready(): %s', e)
