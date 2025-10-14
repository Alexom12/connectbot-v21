"""
Django команда для запуска Telegram бота ConnectBot v21
"""
import os
import asyncio
import logging
import signal
import sys
from django.core.management.base import BaseCommand
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Запуск Telegram бота ConnectBot v21'

    def add_arguments(self, parser):
        parser.add_argument(
            '--debug',
            action='store_true',
            help='Запуск в режиме отладки',
        )

    def handle(self, *args, **options):
        """Основной обработчик команды"""
        # Настройка логирования
        self.setup_logging(debug=options.get('debug', False))
        
        # Проверка токена бота
        if not settings.TELEGRAM_BOT_TOKEN:
            self.stdout.write(
                self.style.ERROR('❌ Ошибка: TELEGRAM_BOT_TOKEN не установлен в настройках')
            )
            self.stdout.write('💡 Добавьте TELEGRAM_BOT_TOKEN=ваш_токен в файл .env')
            return
        
        # Создание папки для логов
        os.makedirs('logs', exist_ok=True)
        
        self.stdout.write("""
🚀 ConnectBot v21
📅 Система корпоративных активностей
🤖 Тайный кофе • Шахматы • Мероприятия
🔧 Версия с планировщиком задач
👑 Админ-панель включена
        """)
        
        # Запуск бота
        try:
            asyncio.run(self.run_bot())
        except KeyboardInterrupt:
            self.stdout.write(self.style.WARNING('\n⏹️ Остановка по команде пользователя'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'💥 Фатальная ошибка: {e}'))
            sys.exit(1)

    def setup_logging(self, debug=False):
        """Настройка логирования"""
        level = logging.DEBUG if debug else logging.INFO
        
        # Создаем форматтер
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        
        # Настраиваем обработчики
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        
        file_handler = logging.FileHandler('logs/bot.log', encoding='utf-8')
        file_handler.setFormatter(formatter)
        
        # Настраиваем логгер
        logger = logging.getLogger()
        logger.setLevel(level)
        logger.addHandler(console_handler)
        logger.addHandler(file_handler)

    async def run_bot(self):
        """Запуск бота"""
        from bots.bot_instance import create_bot_application
        from bots.services.scheduler_service import scheduler_service
        from bots.admin_services import AdminAuthService, AdminStatsService, AdminLogService, SystemHealthService
        
        try:
            self.stdout.write('🚀 Инициализация ConnectBot v21...')
            
            # Создаем приложение бота
            application = create_bot_application()
            if not application:
                self.stdout.write(self.style.ERROR('❌ Не удалось создать приложение бота'))
                return
            
            # Запускаем планировщик задач
            self.stdout.write('📦 Запуск сервисов ConnectBot...')
            scheduler_service.start_scheduler()
            
            # Проверяем статус планировщика
            status = scheduler_service.get_scheduler_status()
            self.stdout.write(f"📅 Планировщик: {status['status']}, задач: {status['job_count']}")
            
            # Показываем информацию о задачах
            for job in status['jobs']:
                self.stdout.write(f"   🎯 {job['name']} -> {job['next_run']}")
            
            self.stdout.write('✅ Все сервисы успешно запущены')
            
            # Запускаем бота
            self.stdout.write('🤖 Запуск Telegram бота (polling)...')
            await application.run_polling(
                drop_pending_updates=True,
                allowed_updates=['message', 'callback_query', 'chat_member']
            )
            
        except KeyboardInterrupt:
            self.stdout.write(self.style.WARNING('⏹️ Остановка по команде пользователя...'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Ошибка работы бота: {e}'))
            raise
        finally:
            # Гарантированная остановка сервисов
            try:
                scheduler_service.stop_scheduler()
                self.stdout.write('✅ Планировщик остановлен')
                self.stdout.write('👋 ConnectBot завершил работу')
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'❌ Ошибка остановки сервисов: {e}'))