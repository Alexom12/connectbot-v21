"""
Упрощенная версия запуска бота для тестирования
"""
import os
import asyncio
import logging

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
django.setup()

async def main():
    """Упрощенный запуск бота"""
    from bots.bot_instance import create_bot_application
    from bots.services.scheduler_service import scheduler_service
    
    print("🚀 Упрощенный запуск ConnectBot...")
    
    try:
        # Создаем бота
        application = create_bot_application()
        if not application:
            print("❌ Не удалось создать бота")
            return
        
        # Запускаем планировщик
        scheduler_service.start_scheduler()
        print("✅ Планировщик запущен")
        
        # Запускаем бота
        print("🤖 Бот запущен (Ctrl+C для остановки)")
        await application.run_polling()
        
    except KeyboardInterrupt:
        print("\n🛑 Остановка...")
    except Exception as e:
        print(f"❌ Ошибка: {e}")
    finally:
        scheduler_service.stop_scheduler()
        print("👋 Бот остановлен")

if __name__ == "__main__":
    # Простая проверка токена
    from django.conf import settings
    if not settings.TELEGRAM_BOT_TOKEN:
        print("❌ TELEGRAM_BOT_TOKEN не установлен!")
        exit(1)
    
    asyncio.run(main())