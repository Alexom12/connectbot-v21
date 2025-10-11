from django.core.management.base import BaseCommand
from bots.services.scheduler_service import scheduler_service
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Запуск планировщика задач ConnectBot'

    def handle(self, *args, **options):
        self.stdout.write('🚀 Запуск планировщика задач...')
        
        try:
            scheduler_service.start_scheduler()
            
            if scheduler_service.is_running:
                self.stdout.write(
                    self.style.SUCCESS('✅ Планировщик задач успешно запущен!')
                )
                
                # Показываем информацию о задачах
                status = scheduler_service.get_scheduler_status()
                self.stdout.write(f"📅 Задач настроено: {status['job_count']}")
                
                for job in status['jobs']:
                    self.stdout.write(f"   • {job['name']} -> {job['next_run']}")
                    
            else:
                self.stdout.write(
                    self.style.ERROR('❌ Не удалось запустить планировщик')
                )
                
        except Exception as e:
            logger.error(f"❌ Ошибка запуска планировщика: {e}")
            self.stdout.write(
                self.style.ERROR(f'❌ Ошибка: {e}')
            )