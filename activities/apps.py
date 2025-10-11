from django.apps import AppConfig

class ActivitiesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'activities'
    verbose_name = 'Активности'
    
    def ready(self):
        # Импортируем сигналы
        try:
            import activities.signals
        except ImportError:
            pass