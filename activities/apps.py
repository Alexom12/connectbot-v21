from django.apps import AppConfig
import os

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

        # Запускаем планировщик только в основном процессе, чтобы избежать дублирования
        if os.environ.get('RUN_MAIN', None) != 'true':
            return
            
        from config import scheduler
        scheduler.start()