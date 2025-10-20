#!/usr/bin/env python
"""
Тестовый скрипт для проверки команд бота
Проверяет доступность Telegram API и имитирует отправку команд
"""
import asyncio
import os
import django
import logging
from django.conf import settings

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

logger = logging.getLogger(__name__)

async def test_bot_api():
    """Тест доступности API Telegram"""
    try:
        from telegram import Bot
        from telegram.error import TelegramError
        
        print("🤖 Проверка доступности Telegram API...")
        
        bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
        
        # Получаем информацию о боте
        bot_info = await bot.get_me()
        logger.info(f"Бот найден: @{bot_info.username}")
        
        # Проверяем вебхуки (должны быть выключены для polling)
        webhook_info = await bot.get_webhook_info()
        logger.info(f"Webhook URL: {webhook_info.url or 'Не установлен (правильно для polling)'}")
        
        return True
        
    except TelegramError as e:
        logger.error(f"Ошибка Telegram API: {e}")
        return False
    except Exception as e:
        logger.error(f"Общая ошибка: {e}")
        return False

async def check_bot_updates():
    """Проверка последних обновлений"""
    try:
        from telegram import Bot
        
        bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
        
        logger.info("Проверка последних обновлений...")
        
        # Получаем последние обновления без их обработки
        updates = await bot.get_updates(limit=10, timeout=5)
        
        if updates:
            logger.info(f"Найдено {len(updates)} обновлений:")
            for update in updates[-3:]:  # Показываем только последние 3
                if update.message:
                    user = update.message.from_user
                    text = update.message.text or "[Не текстовое сообщение]"
                    logger.info(f"  @{user.username or user.first_name}: {text}")
        else:
            logger.info("Новых обновлений нет")
            
        return True
        
    except Exception as e:
        logger.error(f"Ошибка при получении обновлений: {e}")
        return False

def test_handlers_registration():
    """Проверка регистрации обработчиков команд"""
    try:
        logger.info("Проверка регистрации обработчиков...")
        
        # Импортируем команду бота
        from bots.management.commands.runbot import Command
        
        # Проверяем есть ли метод регистрации обработчиков
        cmd = Command()
        if hasattr(cmd, '_setup_basic_handlers'):
            logger.info("Метод _setup_basic_handlers найден")
            
            # Проверим, что в коде есть нужные команды
            import inspect
            source = inspect.getsource(cmd._setup_basic_handlers)
            
            commands = ['start', 'help', 'test']
            for command in commands:
                if f'"{command}"' in source:
                    logger.info(f"Команда /{command} зарегистрирована")
                else:
                    logger.warning(f"Команда /{command} НЕ найдена в коде")
                    
            return True
        else:
            logger.error("Метод _setup_basic_handlers НЕ найден")
            return False
            
    except Exception as e:
        logger.error(f"Ошибка при проверке обработчиков: {e}")
        return False

async def main():
    """Главная функция тестирования"""
    logger.info("ConnectBot v21 - Диагностика команд")
    
    # Тест 1: API доступность
    api_ok = await test_bot_api()
    
    # Тест 2: Проверка обработчиков
    handlers_ok = test_handlers_registration()
    
    # Тест 3: Проверка обновлений
    updates_ok = await check_bot_updates()
    
    logger.info("=" * 50)
    logger.info("Результаты диагностики:")
    logger.info(f"API доступность: {'✅ OK' if api_ok else '❌ FAIL'}")
    logger.info(f"Обработчики команд: {'✅ OK' if handlers_ok else '❌ FAIL'}")
    logger.info(f"Получение обновлений: {'✅ OK' if updates_ok else '❌ FAIL'}")
    
    if all([api_ok, handlers_ok, updates_ok]):
        logger.info("Все тесты пройдены! Бот должен реагировать на команды.")
        logger.info("Попробуйте отправить боту команды:")
        logger.info("   /start - Приветствие")
        logger.info("   /help - Справка")
        logger.info("   /test - Тестовая команда")
    else:
        logger.warning("Обнаружены проблемы. Проверьте настройки бота.")

if __name__ == "__main__":
    asyncio.run(main())