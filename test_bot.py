"""
Самая простая версия бота для тестирования подключения
"""
import asyncio
import logging
from telegram import Bot

# Настройка Django
import os
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
django.setup()

from django.conf import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_simple_bot():
    """Простейший тест бота"""
    bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
    
    try:
        # Проверяем, что бот существует
        logger.info("Получаем информацию о боте...")
        me = await bot.get_me()
        logger.info(f"Успех! Бот: @{me.username} ({me.first_name})")
        
        # Получаем обновления (один раз)
        logger.info("Получаем обновления...")
        updates = await bot.get_updates(limit=1, timeout=5)
        logger.info(f"Получено обновлений: {len(updates)}")
        
        # Устанавливаем webhook на пустой URL (отключаем webhook)
        logger.info("Отключаем webhook...")
        await bot.delete_webhook()
        logger.info("Webhook отключен")
        
        logger.info("Тест завершен успешно!")
        
    except Exception as e:
        logger.error(f"Ошибка: {e}")
    
    finally:
        # Закрываем сессию бота
        if hasattr(bot, '_bot') and hasattr(bot._bot, 'session'):
            await bot._bot.session.close()

if __name__ == '__main__':
    asyncio.run(test_simple_bot())

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    await update.message.reply_text('🤖 ConnectBot работает!')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /help"""
    await update.message.reply_text('Доступные команды:\n/start - начало работы\n/help - справка')

def main():
    """Запуск бота"""
    token = settings.TELEGRAM_BOT_TOKEN
    
    if not token:
        print("❌ TELEGRAM_BOT_TOKEN не установлен")
        return
    
    print(f"🤖 Запуск тестового бота...")
    print(f"📟 Токен: {token[:20]}...")
    
    # Создание приложения
    app = Application.builder().token(token).build()
    
    # Добавление обработчиков
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    
    print("✅ Бот запущен и ожидает сообщений...")
    print("Для остановки нажмите Ctrl+C")
    
    # Запуск polling
    app.run_polling()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n🛑 Бот остановлен")
    except Exception as e:
        print(f"❌ Ошибка: {e}")