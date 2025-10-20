"""
Простая команда для тестирования запуска бота
"""
from django.core.management.base import BaseCommand
from django.conf import settings


class Command(BaseCommand):
    help = 'Простое тестирование настроек бота'

    def handle(self, *args, **options):
        """Проверка настроек и компонентов"""
        
        self.stdout.write('=== ПРОВЕРКА НАСТРОЕК CONNECTBOT ===\n')
        
        # Проверяем токен бота
        if not settings.TELEGRAM_BOT_TOKEN:
            self.stdout.write(
                self.style.ERROR('❌ TELEGRAM_BOT_TOKEN не установлен')
            )
            self.stdout.write('💡 Добавьте TELEGRAM_BOT_TOKEN=ваш_токен в файл .env')
        else:
            self.stdout.write(
                self.style.SUCCESS('✅ TELEGRAM_BOT_TOKEN найден')
            )
        
        # Проверяем импорты
        self.stdout.write('\n=== ПРОВЕРКА ИМПОРТОВ ===')
        
        try:
            from bots.bot_instance import create_bot_application
            self.stdout.write(self.style.SUCCESS('✅ bots.bot_instance - OK'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ bots.bot_instance - ОШИБКА: {e}'))
        
        try:
            from bots.services.scheduler_service import scheduler_service
            self.stdout.write(self.style.SUCCESS('✅ scheduler_service - OK'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ scheduler_service - ОШИБКА: {e}'))
        
        try:
            from bots.services.redis_service import redis_service
            self.stdout.write(self.style.SUCCESS('✅ redis_service - OK'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ redis_service - ОШИБКА: {e}'))
        
        # Проверяем базу данных
        self.stdout.write('\n=== ПРОВЕРКА БАЗЫ ДАННЫХ ===')
        try:
            from employees.models import Employee
            count = Employee.objects.count()
            self.stdout.write(self.style.SUCCESS(f'✅ База данных работает. Сотрудников: {count}'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Ошибка базы данных: {e}'))
        
        self.stdout.write('\n=== ПРОВЕРКА ЗАВЕРШЕНА ===')