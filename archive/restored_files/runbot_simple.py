"""
Простая исполняемая версия бота
"""
import asyncio
import logging
import os
from pathlib import Path

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
django.setup()

from bots.bot_instance import create_bot_application
from bots.services.scheduler_service import scheduler_service

async def main():
    print("🚀 Запуск простого бота...")
    application = create_bot_application()
    if not application:
        print("❌ Не удалось создать приложение бота")
        return
    scheduler_service.start_scheduler()
    try:
        await application.run_polling()
    finally:
        scheduler_service.stop_scheduler()

if __name__ == '__main__':
    from django.conf import settings
    if not settings.TELEGRAM_BOT_TOKEN:
        print("❌ TELEGRAM_BOT_TOKEN не установлен")
        exit(1)
    asyncio.run(main())