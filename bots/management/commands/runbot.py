"""
Основной модуль Telegram бота ConnectBot v21 с планировщиком задач
"""
import os
import asyncio
import logging
import signal
import sys
from django.conf import settings

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
django.setup()

logger = logging.getLogger(__name__)

class ConnectBot:
    def __init__(self):
        self.token = settings.TELEGRAM_BOT_TOKEN
        self.application = None
        self.scheduler = None
    
    async def initialize(self):
        """Инициализация бота и планировщика"""
        try:
            # Импорты внутри функции чтобы избежать циклических импортов
            from bots.bot_instance import create_bot_application
            from bots.services.scheduler_service import scheduler_service
            
            logger.info("🚀 Инициализация ConnectBot v21...")
            
            # Создаем приложение бота
            self.application = create_bot_application()
            if not self.application:
                logger.error("❌ Не удалось создать приложение бота")
                return False
            
            # Инициализируем планировщик
            self.scheduler = scheduler_service
            logger.info("✅ Бот и планировщик инициализированы")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка инициализации: {e}")
            return False
    
    async def start_services(self):
        """Запуск всех сервисов бота"""
        try:
            logger.info("📦 Запуск сервисов ConnectBot...")
            
            # Запускаем планировщик задач
            self.scheduler.start_scheduler()
            
            # Проверяем статус планировщика
            status = self.scheduler.get_scheduler_status()
            logger.info(f"📅 Планировщик: {status['status']}, задач: {status['job_count']}")
            
            # Показываем информацию о задачах
            for job in status['jobs']:
                logger.info(f"   🎯 {job['name']} -> {job['next_run']}")
            
            # Запускаем немедленное создание сессий при старте
            await self.scheduler._create_weekly_sessions_async()
            
            logger.info("✅ Все сервисы успешно запущены")
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка запуска сервисов: {e}")
            return False
    
    async def stop_services(self):
        """Остановка всех сервисов бота"""
        try:
            logger.info("🛑 Остановка сервисов ConnectBot...")
            
            if self.scheduler:
                self.scheduler.stop_scheduler()
                logger.info("✅ Планировщик остановлен")
            
            logger.info("✅ Все сервисы остановлены")
            
        except Exception as e:
            logger.error(f"❌ Ошибка остановки сервисов: {e}")
    
    async def run_bot(self):
        """Запуск polling бота"""
        try:
            if not self.application:
                logger.error("❌ Приложение бота не инициализировано")
                return
            
            logger.info("🤖 Запуск Telegram бота (polling)...")
            await self.application.run_polling(
                drop_pending_updates=True,
                allowed_updates=['message', 'callback_query', 'chat_member']
            )
            
        except Exception as e:
            logger.error(f"❌ Ошибка работы бота: {e}")
            raise
    
    async def run(self):
        """Основной метод запуска бота"""
        try:
            # Инициализация
            if not await self.initialize():
                return
            
            # Запуск сервисов
            if not await self.start_services():
                return
            
            # Запуск бота
            await self.run_bot()
            
        except KeyboardInterrupt:
            logger.info("⏹️ Остановка по команде пользователя...")
        except Exception as e:
            logger.error(f"💥 Критическая ошибка: {e}")
        finally:
            # Гарантированная остановка сервисов
            await self.stop_services()
            logger.info("👋 ConnectBot завершил работу")

def signal_handler(signum, frame):
    """Обработчик сигналов для graceful shutdown"""
    print(f"\n🛑 Получен сигнал {signum}. Остановка ConnectBot...")
    
    # Останавливаем event loop
    loop = asyncio.get_event_loop()
    for task in asyncio.all_tasks(loop):
        task.cancel()
    
    sys.exit(0)

def setup_logging():
    """Настройка логирования"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('logs/bot.log', encoding='utf-8')
        ]
    )

def main():
    """Основная функция запуска бота"""
    # Настройка логирования
    setup_logging()
    
    # Регистрация обработчиков сигналов
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Создание и запуск бота
    bot = ConnectBot()
    
    try:
        # Запуск асинхронного бота
        asyncio.run(bot.run())
    except KeyboardInterrupt:
        logger.info("⏹️ Остановка по команде пользователя")
    except Exception as e:
        logger.error(f"💥 Фатальная ошибка: {e}")
        sys.exit(1)

if __name__ == "__main__":
    # Проверка токена бота
    if not settings.TELEGRAM_BOT_TOKEN:
        print("❌ Ошибка: TELEGRAM_BOT_TOKEN не установлен в настройках")
        print("💡 Добавьте TELEGRAM_BOT_TOKEN=ваш_токен в файл .env")
        sys.exit(1)
    
    # Проверка существования папки logs
    os.makedirs('logs', exist_ok=True)
    
    print("""
    🚀 ConnectBot v21
    📅 Система корпоративных активностей
    🤖 Тайный кофе • Шахматы • Мероприятия
    🔧 Версия с планировщиком задач
    """)
    
    main()