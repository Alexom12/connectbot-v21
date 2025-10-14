"""
Простая команда для запуска Telegram бота без планировщика
"""
import logging
import sys
from django.core.management.base import BaseCommand
from django.conf import settings

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Простой запуск Telegram бота ConnectBot v21'

    def handle(self, *args, **options):
        """Основной обработчик команды"""
        # Настройка логирования
        self.setup_logging()
        
        # Проверка токена бота
        if not settings.TELEGRAM_BOT_TOKEN:
            self.stdout.write(
                self.style.ERROR('Ошибка: TELEGRAM_BOT_TOKEN не установлен в настройках')
            )
            self.stdout.write('Добавьте TELEGRAM_BOT_TOKEN=ваш_токен в файл .env')
            return
        
        self.stdout.write("""
ConnectBot v21 - Простой запуск
Система корпоративных активностей
Telegram бот запускается...
        """)
        
        # Запуск бота
        try:
            from bots.bot_instance import create_bot_application
            
            self.stdout.write('Инициализация бота...')
            
            # Создаем приложение бота
            application = create_bot_application()
            if not application:
                self.stdout.write(self.style.ERROR('Не удалось создать приложение бота'))
                return
            
            self.stdout.write('Бот создан успешно!')
            self.stdout.write('Запуск polling... (Ctrl+C для остановки)')
            
            # Запуск в режиме polling без планировщика
            application.run_polling(
                drop_pending_updates=True,
                allowed_updates=['message', 'callback_query', 'chat_member']
            )
            
        except KeyboardInterrupt:
            self.stdout.write(self.style.WARNING('\nОстановка по команде пользователя'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Ошибка: {e}'))
            import traceback
            traceback.print_exc()

    def setup_logging(self):
        """Настройка логирования"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(sys.stdout)
            ]
        )