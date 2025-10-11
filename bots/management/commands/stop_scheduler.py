from django.core.management.base import BaseCommand
from bots.services.scheduler_service import scheduler_service
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Остановка планировщика задач ConnectBot'

    def handle(self, *args, **options):
        self.stdout.write('🛑 Остановка планировщика задач...')
        
        try:
            scheduler_service.stop_scheduler()
            self.stdout.write(
                self.style.SUCCESS('✅ Планировщик задач остановлен!')
            )
                
        except Exception as e:
            logger.error(f"❌ Ошибка остановки планировщика: {e}")
            self.stdout.write(
                self.style.ERROR(f'❌ Ошибка: {e}')
            )