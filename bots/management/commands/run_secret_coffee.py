from django.core.management.base import BaseCommand
from bots.services.matching_service_client import run_matching_for_active_employees
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Запускает процесс подбора пар "Секретный кофе" через новый API-клиент.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("Начинаем подбор пар для 'Секретного кофе'..."))
        
        try:
            pairs = run_matching_for_active_employees()
            
            if pairs is None:
                self.stdout.write(self.style.ERROR("Произошла ошибка во время подбора. См. логи для деталей."))
                return

            if not pairs:
                self.stdout.write(self.style.WARNING("Не найдено пар для 'Секретного кофе'."))
            else:
                self.stdout.write(self.style.SUCCESS(f"Успешно сформировано {len(pairs)} пар:"))
                for pair in pairs:
                    self.stdout.write(f"  - Пара: {pair[0]} и {pair[1]}")
            
            # Здесь в будущем будет логика сохранения пар и отправки уведомлений
            
        except Exception as e:
            logger.error(f"Критическая ошибка в команде run_secret_coffee: {e}", exc_info=True)
            self.stdout.write(self.style.ERROR(f"Произошла критическая ошибка: {e}"))

